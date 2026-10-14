import pyodbc
SERVER = r'.\SQLEXPRESS'
DATABASE = 'BD_MODERNIZACION'

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate = yes"
)

try:
    print("Conectando a SQL Server...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("SELECT @@VERSION;")
    row = cursor.fetchone()

    print("\n¡Conexión exitosa!")
    print(f"Versión detectada:\n{row[0]}")

    conn.close()
except Exception as e:
    print("\nError al conectar:")
    print(e)