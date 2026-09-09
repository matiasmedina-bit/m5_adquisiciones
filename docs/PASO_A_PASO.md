# PASO A PASO para levantar el sistema (Windows + VS Code)

> Sigue los pasos **en orden**. No te saltes ninguno. Cada paso dice **qué deberías ver** si salió bien.

---

## PASO 0 — Guardar el archivo .env

Ya tienes el `.env` escrito (está perfecto). Pero fíjate: en la pestaña del archivo, arriba, hay un **puntito blanco ●**. Eso significa que NO está guardado.

👉 Haz clic en la pestaña del `.env` y apreta **Ctrl + S**.
El puntito ● se convierte en una **X**. Listo, ya quedó guardado.

---

## PASO 1 — Abrir la terminal DENTRO de VS Code

En el menú de arriba de VS Code:
**Terminal → New Terminal** (o apreta `Ctrl + ñ`).

Abajo se abre una terminal. Fíjate que la ruta que aparece termine en `m5_adquisiciones` (la carpeta del proyecto). Algo como:

```
PS C:\Users\TuNombre\...\m5_adquisiciones>
```

✅ **Qué deberías ver:** la terminal abierta, apuntando a la carpeta `m5_adquisiciones`.

> Si la ruta NO termina en `m5_adquisiciones`, escribe `cd` y arrastra la carpeta del proyecto a la terminal, luego Enter.

---

## PASO 2 — Crear el entorno virtual

Copia y pega esto en la terminal, y Enter:

```powershell
python -m venv venv
```

Espera unos segundos (no muestra nada, es normal). Se crea una carpeta nueva llamada `venv` en el proyecto.

✅ **Qué deberías ver:** vuelve a aparecer el `PS C:\...>` sin errores, y en el explorador de la izquierda aparece una carpeta `venv`.

---

## PASO 3 — Activar el entorno virtual

```powershell
venv\Scripts\activate
```

✅ **Qué deberías ver:** ahora la línea de la terminal empieza con **`(venv)`**, así:

```
(venv) PS C:\Users\...\m5_adquisiciones>
```

> ⚠️ **Si te sale un error rojo** que dice algo de *"ejecución de scripts está deshabilitada"* (execution policy), pega ESTO primero y dale Enter:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> Y vuelve a correr `venv\Scripts\activate`. Ahora sí debería salir el `(venv)`.

**IMPORTANTE:** de aquí en adelante, la terminal SIEMPRE debe mostrar `(venv)` al inicio. Si cierras la terminal y la vuelves a abrir, repite este Paso 3.

---

## PASO 4 — Instalar las dependencias

Con el `(venv)` activado:

```powershell
pip install -r requirements.txt
```

Esto descarga Django y lo demás. Demora entre 30 segundos y 2 minutos.
En el Incremento 2 se agregaron **reportlab** y **pillow** (generan el PDF de la
Orden de Compra con el logo, RF-26).

✅ **Qué deberías ver:** varias líneas que terminan con algo como
`Successfully installed Django-5.0.6 psycopg2-binary-2.9.9 python-dotenv-1.0.1 reportlab-4.2.2 pillow-10.4.0`

---

## PASO 5 — Crear las tablas en la base de datos

Son DOS comandos, uno después del otro:

```powershell
python manage.py makemigrations
```

✅ Deberías ver `No changes detected` (las migraciones del Incremento 2 ya vienen
escritas en el repo) **o** una lista corta de `Migrations for '...'`. Ambos casos
son correctos: si genera algo, el siguiente comando lo aplica igual.

```powershell
python manage.py migrate
```

✅ Deberías ver muchas líneas con `Applying ... OK`, incluidas las apps nuevas
`adquisiciones` y `facturacion`.

> ⚠️ **Si en este paso sale un error de contraseña o conexión**, salta al final de este archivo (sección "SI ALGO FALLA").

---

## PASO 6 — Cargar los datos de demostración

```powershell
python manage.py seed_demo
```

✅ **Qué deberías ver:** mensajes como `Usuario creado: admin / demo12345` y al final `Usuarios: admin / jefe / encargado / bodega / contador (clave: demo12345)`.
También crea la cadena de demostración del Incremento 2: cotizaciones, órdenes de compra, movimientos de bodega y una factura.

---

## PASO 7 — Prender el servidor

```powershell
python manage.py runserver
```

✅ **Qué deberías ver:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## PASO 8 — Entrar al sistema

Abre tu navegador (Chrome, etc.) y ve a:

**http://127.0.0.1:8000/**

Inicia sesión con:
- Usuario: **admin**
- Clave: **demo12345**

🎉 ¡Ahí está el sistema funcionando!

> Para **apagar** el servidor: vuelve a la terminal y apreta `Ctrl + C`.

---

## Para correr las PRUEBAS (lo que pide la rúbrica)

Apaga el servidor (`Ctrl + C`), y con el `(venv)` activado:

```powershell
python manage.py test --verbosity=2
```

✅ Al final debe decir `OK` y la cantidad de tests. **Toma una captura de pantalla** de eso para el informe de pruebas.

---

# SI ALGO FALLA

### "password authentication failed for user postgres"
La contraseña del `.env` no coincide con la de PostgreSQL.
- Abre el `.env` y revisa que `DB_PASSWORD=matias1234` sea EXACTAMENTE tu contraseña de PostgreSQL.
- Guarda con Ctrl+S y vuelve a intentar el Paso 5.

### "could not connect to server" / "Connection refused"
Puede que tu PostgreSQL 18 esté en otro puerto (tú tienes 2 servidores en pgAdmin).
- En pgAdmin, clic derecho sobre el servidor **LocalHost** → **Properties** → pestaña **Connection** → mira el campo **Port**.
- Si NO dice 5432 (por ejemplo dice 5433), cambia en tu `.env` la línea `DB_PORT=` a ese número, guarda y reintenta.

### "database m5_adquisiciones does not exist"
La base no quedó creada. En pgAdmin: clic derecho en **Databases → Create → Database**, nombre `m5_adquisiciones`, Save.

### "No module named 'dotenv'" o "No module named 'django'"
No tienes el `(venv)` activado o no instalaste. Repite Paso 3 y Paso 4.

### La terminal no muestra "(venv)"
Repite el Paso 3. Si da error de execution policy, usa el comando `Set-ExecutionPolicy` de la nota del Paso 3.
