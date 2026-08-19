# Recursos para el empaquetado

## Carpeta `python/` (Python embebido)

No se versiona en Git (está en `.gitignore`). Se genera en su máquina con:

```powershell
cd <raíz del repositorio>
.\scripts\setup_embedded_python.ps1
```

Eso descarga el **Windows embeddable** oficial (x64), activa `import site`, instala **pip** y las dependencias de `backend/requirements.txt` dentro de `python/`.

Luego, desde `desktop/`:

```powershell
npm run dist
```

**electron-builder** copia `resources/python` al instalador; la app usará `resources/python/python.exe` antes que el Python del sistema.

Para regenerar desde cero: `.\scripts\setup_embedded_python.ps1 -Force`

### Instalador sin Python embebido

Si prefiere que el cliente use solo Python del sistema: en `desktop/package.json` quite la entrada `resources/python` de `extraResources` y en el script `dist` elimine `node check-embedded-python.cjs &&`.
