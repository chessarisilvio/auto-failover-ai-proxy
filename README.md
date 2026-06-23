# Auto-Failover AI Proxy

## Descrizione
Sistema di failover automatico per proxy AI locali che monitora la salute di un endpoint primario e reindirizza il traffico a un endpoint di backup in caso di timeout o risposta lenta.

## Architettura
- **health_check.sh**: script Bash che verifica la latenza dell'endpoint primario tramite curl.
- **proxy_router.py**: router Python che ascolta su una porta locale e inoltra le richieste all'endpoint attivo (primario o secondario) in base al risultato dello health check.
- **Servizi systemd**: 
  - `auto-failover-health.service`: esegue periodicamente lo health check e aggiorna una variabile d'ambiente o un file di stato.
  - `auto-failover-router.service`: avvia il router Python.
  - Timer associato per lo health check.

## Installazione
1. Clonare il repository nella directory desiderata.
2. Copiare i file di servizio systemd in `~/.config/systemd/user/`:
   ```bash
   cp auto-failover-health.service ~/.config/systemd/user/
   cp auto-failover-health.timer ~/.config/systemd/user/
   cp auto-failover-router.service ~/.config/systemd/user/
   ```
3. Ricaricare il daemon systemd:
   ```bash
   systemctl --user daemon-reload
   ```
4. Abilitare e avviare i servizi:
   ```bash
   systemctl --user enable --now auto-failover-health.timer
   systemctl --user enable --now auto-failover-router.service
   ```

## Uso
- Il router ascolta su `localhost:9292` (configurabile) e inoltra a:
  - Primario: `localhost:8090` (default)
  - Secondario: `localhost:8081` (default)
- Lo health check verifica il primario ogni minuto (tramite timer) e imposta una variabile d'ambiente o un file che il router legge per decidere l'endpoint attivo.
- Variabili d'ambiente configurabili:
  - `PROXY_HOST_PRIMARY`, `PROXY_PORT_PRIMARY`
  - `PROXY_HOST_SECONDARY`, `PROXY_PORT_SECONDARY`
  - `PROXY_LISTEN_HOST`, `PROXY_LISTEN_PORT`
  - `HEALTH_CHECK_THRESHOLD_MS`

## Esempi
```bash
# Test manuale dello health check
PROXY_HOST=localhost PROXY_PORT=8090 THRESHOLD_MS=200 ./health_check.sh && echo "OK" || echo "FAIL"

# Verifica lo stato dei servizi
systemctl --user status auto-failover-health.timer
systemctl --user status auto-failover-router.service
```

## Stato
✅ COMPLETATO — 2026-06-16
Tutte le funzionalità implementate e testate: health check, router di fallback, servizi systemd con timer.