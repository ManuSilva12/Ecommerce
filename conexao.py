import mysql.connector

def conectar():
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # coloque a senha do root se tiver
            database="ecommerce",  # nome do seu banco
            unix_socket="/opt/lampp/var/mysql/mysql.sock"
        )
        print("✅ Conectado ao MySQL com sucesso!")
        return conexao
    except mysql.connector.Error as err:
        print(f"[ERRO] Falha na conexão: {err}")
        return None

# --- Teste rápido de conexão ---
if __name__ == "__main__":
    conectar()
