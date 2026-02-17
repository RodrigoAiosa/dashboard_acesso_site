import psycopg2
from tabulate import tabulate

# Configurações do seu console Aiven
config = {
    "host": "pg-2e2874e2-rodrigoaiosa-skydatasoluction.l.aivencloud.com",
    "port": "13191",
    "database": "defaultdb",
    "user": "avnadmin",
    "password": "AVNS_LlZukuJoh_0Kbj0dhvK", 
    "sslmode": "require"
}

def ver_controle_acesso():
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Ajuste direto: Subtraímos 3 horas da coluna data_hora
        # Isso corrige o erro onde o banco exibe 22h quando deveria ser 16h.
        query = """
            SELECT 
                id_acesso, 
                TO_CHAR(data_hora - INTERVAL '3 hours', 'DD/MM/YYYY HH24:MI:SS') as data_br,
                dispositivo, 
                navegador, 
                ip, 
                pagina, 
                acao, 
                duracao 
            FROM controle_acesso_site
            WHERE duracao <> '00:00'
            ORDER BY data_hora DESC;
        """
        
        cursor.execute(query)
        linhas = cursor.fetchall()
        
        colunas = ["ID", "Data/Hora (BR)", "Disp.", "Navegador", "IP", "Página", "Ação", "Duração"]
        
        print("\n=== LOG DE ACESSOS NO BD_SKYDATA (Horário de Brasília) ===")
        if linhas:
            print(tabulate(linhas, headers=colunas, tablefmt="grid"))
        else:
            print("ℹ️ Nenhum registro de acesso encontrado.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao consultar logs: {e}")

if __name__ == "__main__":
    ver_controle_acesso()
