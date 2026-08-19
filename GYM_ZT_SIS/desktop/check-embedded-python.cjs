'use strict';

const fs = require('fs');
const path = require('path');

const exe = path.join(__dirname, 'resources', 'python', 'python.exe');

if (!fs.existsSync(exe)) {
  console.error(
    '\n[Falta Python embebido] No existe: resources\\python\\python.exe\n' +
      'Desde la raíz del repositorio ejecute:\n' +
      '  .\\scripts\\setup_embedded_python.ps1\n' +
      'Luego vuelva a ejecutar npm run dist.\n'
  );
  process.exit(1);
}
