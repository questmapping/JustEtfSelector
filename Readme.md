# Considerazioni
Utilizzando invece il servizio streamlit share è possibile posizionare in files sicuri le nostre chiavi di accesso: https://www.notion.so/Secrets-Management-730c82af2fc048d383d668c4049fb9bf

# Cosa Serve
Un account su justetf.com e caricare i files delle liste da qualche parte accessibile (tipo dropbox o simili). Le liste sono state fatte un po di tempo fa, quindi non è detto che siano ancora attendibili.

# Build and deploy on Streamlit Share
Basta registrarsi e seguire la procedura guidata. Per le chiavi di accesso di JustEtf basta inserire la sezione:

```
[je_credentials]
username = "my_JustEtf_username"
password = "my_JustEtf_password"

[files_position]
full_list = "urlTo/etf_list.txt"
accumulating_list = "urlTo/accumulating.txt"
distributing_list = "urlTo/distributing.txt"
datadump = "urlTo/full_etfs.json"
```

In locale, questa parte va inserita nel file secrets.toml (ovviamente da inserire in .gitignore dopo averlo creato) come indicato da https://www.notion.so/Secrets-Management-730c82af2fc048d383d668c4049fb9bf

# Primca cosa da fare
E' il dump dei dati aggiornati con python datadump.py