use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;

/// Sidecar state — holds the backend child process
struct Sidecar(Mutex<Option<Child>>);

/// Health status for the sidecar
#[derive(Clone, serde::Serialize)]
struct SidecarHealth {
    running: bool,
    pid: Option<u32>,
    uptime_seconds: u64,
    restart_count: u32,
    last_health_check: String,
    backend_responsive: bool,
}

/// Counter for restarts
struct RestartCounter(Mutex<(u32, std::time::Instant)>);

fn spawn_python_backend() -> Option<Child> {
    // === Release mode: try bundled sidecar binary first ===
    let sidecar_path = find_sidecar_binary();
    if let Some(sidecar) = sidecar_path {
        log::info!("Starting bundled sidecar from {:?}", sidecar);
        match Command::new(&sidecar)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
        {
            Ok(child) => {
                log::info!("Sidecar binary started (pid {}) — RELEASE MODE", child.id());
                return Some(child);
            }
            Err(e) => {
                log::warn!("Sidecar binary found but failed to start: {} — falling back to Python", e);
            }
        }
    }

    // === Dev mode: use Python venv or system Python ===
    let engine_dir = std::env::current_dir()
        .ok()
        .map(|p| p.join("engine"))
        .or_else(|| {
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|x| x.join("engine")))
        })
        .unwrap_or_else(|| std::path::PathBuf::from("engine"));

    let venv_python = if cfg!(target_os = "windows") {
        engine_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        engine_dir.join(".venv").join("bin").join("python")
    };

    let python = if venv_python.exists() {
        venv_python
    } else {
        std::path::PathBuf::from("python")
    };

    log::info!(
        "Starting Python sidecar from {:?} with {:?} — DEV MODE",
        engine_dir,
        python
    );

    match Command::new(&python)
        .args([
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-access-log",
        ])
        .current_dir(&engine_dir)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
    {
        Ok(child) => {
            log::info!("Python sidecar started (pid {})", child.id());
            Some(child)
        }
        Err(e) => {
            log::error!("Failed to start Python sidecar: {}", e);
            None
        }
    }
}

/// Find the sidecar binary — checks multiple locations:
/// 1. Next to the executable (release bundle)
/// 2. In src-tauri/binaries (dev build)
fn find_sidecar_binary() -> Option<std::path::PathBuf> {
    let sidecar_name = if cfg!(target_os = "windows") {
        "channelforge-engine-x86_64-pc-windows-msvc.exe"
    } else if cfg!(target_os = "macos") {
        "channelforge-engine-aarch64-apple-darwin"
    } else {
        "channelforge-engine-x86_64-unknown-linux-gnu"
    };

    // 1. Next to the current executable (Tauri bundle)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let sidecar = exe_dir.join(sidecar_name);
            if sidecar.exists() {
                return Some(sidecar);
            }
        }
    }

    // 2. In src-tauri/binaries (dev)
    if let Ok(cwd) = std::env::current_dir() {
        let sidecar = cwd.join("src-tauri").join("binaries").join(sidecar_name);
        if sidecar.exists() {
            return Some(sidecar);
        }
    }

    None
}

/// Check if backend is responsive
fn check_backend_health() -> bool {
    match std::net::TcpStream::connect_timeout(
        &"127.0.0.1:8000".parse().unwrap(),
        std::time::Duration::from_secs(2),
    ) {
        Ok(_) => true,
        Err(_) => false,
    }
}

/// Get sidecar health status
#[tauri::command]
fn get_sidecar_health(
    state: tauri::State<'_, Sidecar>,
    counter: tauri::State<'_, RestartCounter>,
) -> SidecarHealth {
    let running = if let Ok(guard) = state.0.lock() {
        guard.is_some()
    } else {
        false
    };

    let (restart_count, start_time) = if let Ok(guard) = counter.0.lock() {
        (guard.0, guard.1)
    } else {
        (0, std::time::Instant::now())
    };

    let pid = if let Ok(guard) = state.0.lock() {
        guard.as_ref().map(|c| c.id())
    } else {
        None
    };

    SidecarHealth {
        running,
        pid,
        uptime_seconds: start_time.elapsed().as_secs(),
        restart_count,
        last_health_check: chrono::Utc::now().to_rfc3339(),
        backend_responsive: check_backend_health(),
    }
}

/// Restart the sidecar
#[tauri::command]
fn restart_sidecar(
    state: tauri::State<'_, Sidecar>,
    counter: tauri::State<'_, RestartCounter>,
) -> String {
    // Kill existing
    if let Ok(mut guard) = state.0.lock() {
        if let Some(ref mut child) = *guard {
            log::info!("Killing existing sidecar (pid {})", child.id());
            let _ = child.kill();
            let _ = child.wait();
        }
        // Spawn new
        *guard = spawn_python_backend();
    }
    // Increment counter
    if let Ok(mut guard) = counter.0.lock() {
        guard.0 += 1;
    }
    "Sidecar restarted".to_string()
}

/// Get system diagnostics
#[tauri::command]
fn get_diagnostics() -> serde_json::Value {
    let engine_dir = std::env::current_dir()
        .ok()
        .map(|p| p.join("engine"))
        .unwrap_or_else(|| std::path::PathBuf::from("engine"));

    let venv_exists = if cfg!(target_os = "windows") {
        engine_dir.join(".venv").join("Scripts").join("python.exe").exists()
    } else {
        engine_dir.join(".venv").join("bin").join("python").exists()
    };

    let db_exists = engine_dir.join("data").join("channelforge.db").exists();
    let env_exists = engine_dir.join(".env").exists();
    let data_dir = engine_dir.join("data");
    let workspaces_dir = data_dir.join("workspaces");

    serde_json::json!({
        "engine_dir": engine_dir.to_string_lossy(),
        "venv_exists": venv_exists,
        "db_exists": db_exists,
        "env_exists": env_exists,
        "data_dir_exists": data_dir.exists(),
        "workspaces_dir_exists": workspaces_dir.exists(),
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "tauri_version": "2.x",
        "app_version": "5.8.0",
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let child = spawn_python_backend();
            app.manage(Sidecar(Mutex::new(child)));
            app.manage(RestartCounter(Mutex::new((0, std::time::Instant::now()))));

            // Auto-restart watcher (check every 15 seconds)
            let app_handle = app.handle().clone();
            std::thread::spawn(move || {
                std::thread::sleep(std::time::Duration::from_secs(10)); // Initial delay
                loop {
                    std::thread::sleep(std::time::Duration::from_secs(15));
                    if !check_backend_health() {
                        log::warn!("Backend not responsive, attempting restart...");
                        if let Some(state) = app_handle.try_state::<Sidecar>() {
                            if let Ok(mut guard) = state.0.lock() {
                                if let Some(ref mut child) = *guard {
                                    let _ = child.kill();
                                    let _ = child.wait();
                                }
                                *guard = spawn_python_backend();
                            }
                        }
                        if let Some(counter) = app_handle.try_state::<RestartCounter>() {
                            if let Ok(mut guard) = counter.0.lock() {
                                guard.0 += 1;
                                if guard.0 > 5 {
                                    log::error!("Sidecar restarted {} times, stopping auto-restart", guard.0);
                                    break;
                                }
                            }
                        }
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_sidecar_health,
            restart_sidecar,
            get_diagnostics,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|_app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            if let Some(state) = _app_handle.try_state::<Sidecar>() {
                if let Ok(mut guard) = state.0.lock() {
                    if let Some(ref mut child) = *guard {
                        log::info!("Killing Python sidecar (pid {})", child.id());
                        let _ = child.kill();
                    }
                }
            }
        }
    });
}
