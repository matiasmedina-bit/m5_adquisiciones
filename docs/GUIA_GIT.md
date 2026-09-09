# Guía de Git e Informe de Commits — Grupo 23

**Integrantes (3):** Cristóbal López · Emiliano Fernández · Matías Medina

La rúbrica exige que **todos los integrantes** tengan commits en el repositorio y que se entregue un **informe con los commits de cada uno**. Esta guía deja el reparto listo para que cada uno haga sus propios commits con su cuenta.

> **Importante:** cada integrante debe hacer commits **desde su propio computador y su propia cuenta de Git**. No vale que una sola persona haga todos los commits.

---

## 1. Configuración inicial (lo hace UNO solo, el que arma el repo)

```bash
# Dentro de la carpeta m5_adquisiciones
git init
git add .gitignore README.md requirements.txt .env.example
git commit -m "chore: configuracion inicial del repositorio"

# Crear el repositorio en GitHub y enlazarlo:
git remote add origin <URL_DEL_REPOSITORIO>
git branch -M main
git push -u origin main
```

Luego los otros dos clonan:

```bash
git clone <URL_DEL_REPOSITORIO>
cd m5_adquisiciones
```

## 2. Que cada integrante configure su identidad

**Cada uno, en su máquina, una sola vez:**

```bash
git config user.name "Nombre Apellido"
git config user.email "tu-correo@ejemplo.cl"
```

Usen el correo asociado a su cuenta de GitHub para que los commits queden atribuidos correctamente.

---

## 3. Reparto de commits por integrante

Cada integrante hace `commit` de los archivos de su parte. Así el `git log` muestra participación real de los 3.

### Emiliano Fernández — Seguridad / Usuarios + Infraestructura
```bash
git add usuarios/ config/ templates/base.html templates/home.html templates/registration/ templates/usuarios/ static/
git commit -m "feat(seguridad): autenticacion, cuentas y roles RBAC (CU-50, 51, 52) + infraestructura base"
git add usuarios/tests.py
git commit -m "test(usuarios): pruebas de validacion RUT, modelo y control de acceso"
```

### Cristóbal López — Proveedores + Proyectos
```bash
git add proveedores/ templates/proveedores/ proyectos/ templates/proyectos/
git commit -m "feat(proveedores-proyectos): registro y validacion de proveedores (CU-01 a 05) e itemizado (CU-06 a 10)"
git add proveedores/tests.py proyectos/tests.py
git commit -m "test(proveedores-proyectos): pruebas de RUT duplicado, saldo de itemizado y validaciones"
```

### Matías Medina — Solicitudes + Inventario + Datos demo
```bash
git add solicitudes/ templates/solicitudes/ inventario/ templates/inventario/ usuarios/management/
git commit -m "feat(solicitudes): generacion, edicion y aprobacion de solicitudes (CU-11, 12, 14, 16, 17) y datos demo"
git add solicitudes/tests.py inventario/tests.py
git commit -m "test(solicitudes): pruebas de correlativo, flujo enviar/aprobar y detalle"
```

Después de cada commit, suban con:
```bash
git push
```

---

## 4. Generar el informe de commits

Una vez que los 3 hayan subido sus commits:

### Informe completo (uno por línea)
```bash
git log --pretty=format:"%h | %an | %ad | %s" --date=short > docs/informe_commits.txt
```

### Resumen de cuántos commits hizo cada uno
```bash
git shortlog -sn --all
```

Salida esperada (demuestra que participaron los 3):
```
  2  Cristóbal López
  2  Emiliano Fernández
  2  Matías Medina
```

### Commits de un integrante específico
```bash
git log --author="López" --pretty=format:"%h %ad %s" --date=short
```

Peguen la salida de `git shortlog -sn` y/o el contenido de `docs/informe_commits.txt` en el documento del incremento como evidencia de versionamiento.

---

## 5. Checklist final de Git

- [ ] Repositorio creado y enlazado al remoto
- [ ] Los 3 integrantes configuraron su `user.name` y `user.email`
- [ ] Cada integrante hizo al menos un commit con su cuenta
- [ ] `git shortlog -sn` muestra a los 3 integrantes
- [ ] Informe de commits generado en `docs/informe_commits.txt`
- [ ] Acceso al repositorio compartido con el profesor (si lo solicita)
