# by.b

Ferramenta pessoal de linha de comando com duas partes:

1. **recon** — testes de segurança no seu próprio site (`byb.dev.br`): headers HTTP,
   certificado TLS, DNS, `robots.txt` e portas comuns abertas.
2. **deadman** — Dead Man's Switch: se você não fizer check-in dentro do prazo,
   uma mensagem é enviada automaticamente pro seu WhatsApp via CallMeBot.

⚠️ O `recon` deve ser usado **apenas em domínios que são seus** ou que você tem
autorização explícita para testar.

## Instalação no Termux

```bash
pkg install python
cd by.b
pip install -e .
```

Isso instala o comando `by.b` disponível globalmente no Termux.

## 1. Configurar o Dead Man's Switch

### 1.1 Ativar o CallMeBot (só precisa fazer uma vez)

1. Salve este número na agenda do seu WhatsApp: `+34 644 59 71 67`
2. Envie pra ele, pelo WhatsApp, a mensagem: `I allow callmebot to send me messages`
3. Você vai receber uma resposta com sua **apikey** pessoal.

### 1.2 Editar o `config.json`

Abra `config.json` e preencha:

```json
{
  "deadman": {
    "prazo_horas": 48,
    "mensagem": "sua mensagem de alerta aqui",
    "api_token": "invente-um-token-secreto-aleatorio-aqui"
  },
  "whatsapp": {
    "telefone": "5531999999999",
    "apikey": "a apikey que o CallMeBot te enviou"
  }
}
```

- `prazo_horas`: quantas horas sem check-in até disparar o alerta.
- `api_token`: uma senha que só você e o botão do HTML vão saber (invente uma string longa e aleatória).
- `telefone`: o número **de quem vai receber o alerta** (com código do país, sem `+` nem espaços).

## 2. Rodar o switch

```bash
by.b deadman serve
```

Isso sobe uma API na porta **5005** e já começa a contar o tempo. Deixe essa
sessão do Termux rodando (igual você já faz com o `ttyd`).

Comandos úteis:
```bash
by.b deadman status     # ver quanto tempo falta
by.b deadman checkin    # resetar o cronômetro manualmente, pelo terminal
```

## 3. Expor a API pro botão do HTML

Como o `cloudflared` do túnel nomeado (aquele do passo 6 que já configuramos)
só aponta pra uma porta, adicione uma segunda regra no `~/.cloudflared/config.yml`:

```yaml
tunnel: meu-termux
credentials-file: /data/data/com.termux/files/home/.cloudflared/<ID-DO-TUNEL>.json
ingress:
  - hostname: termux.seudominio.com
    service: http://localhost:7681
  - hostname: deadman.seudominio.com
    service: http://localhost:5005
  - service: http_status:404
```

E crie a rota de DNS pra esse novo subdomínio:

```bash
cloudflared tunnel route dns meu-termux deadman.seudominio.com
```

Reinicie o túnel (`cloudflared tunnel run meu-termux`) e a API do switch já
fica acessível publicamente em `https://deadman.seudominio.com`.

## 4. Testar o recon

```bash
by.b recon https://byb.dev.br
```

Devolve um relatório em JSON com headers de segurança, validade do certificado,
DNS, `robots.txt` e portas comuns abertas.

## Segurança

- O `api_token` do `config.json` é a única coisa protegendo o botão de check-in
  — trate como senha. Nunca deixe esse arquivo público num repositório Git.
- O CallMeBot é um serviço de terceiros gratuito para uso pessoal; não é
  adequado para envio em massa ou uso comercial.
