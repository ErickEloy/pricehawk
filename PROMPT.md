# pricehawk — Monitor de preços white-label com alertas

Cole o bloco abaixo no claude-free (aberto nesta pasta):

```
Crie o projeto "pricehawk": monitor de preços white-label (qualquer loja configurável).
- Lojas configuradas por YAML (seletor de preço, nome, disponibilidade); demo com fakestoreapi.com e books.toscrape.com.
- Agendamento com APScheduler, histórico em SQLite, alerta quando o preço cai X% (Telegram e Discord via webhook).
- Dashboard Next.js com gráfico de histórico por produto e tema/cores configuráveis (white-label).
- docker-compose, testes.

Regras gerais:
- Trabalhe SOMENTE dentro desta pasta: C:\Users\erick\Documents\Projetos Pessoais\pricehawk
- Etapas pequenas; ao fim de cada etapa rode os testes e faça um commit (Conventional Commits).
- Nunca commite segredos: use .env.example e coloque .env no .gitignore.
- README em português e inglês, com diagrama da arquitetura em mermaid, como rodar, prints/GIF e roadmap.
- Licença MIT, GitHub Actions (lint com ruff/eslint + testes).
- No final: git push para o remoto origin.
```
