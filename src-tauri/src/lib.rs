use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;

struct Sidecar(Mutex<Option<Child>>);

fn spawn_python_backend() -> Option<Child> {
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
        "Starting Python sidecar from {:?} with {:?}",
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

            Ok(())
        })
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
