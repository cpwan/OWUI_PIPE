# OWUI_PIPE

> Based on https://openwebui.com/f/coleam/n8n_pipe

This repo contains pipe for OpenWebUI integration.

## n8n Agent

### Setups
1. Import from the example `n8n_agent_demo.json`

    <img src="static/n8n-import-workflow.png" alt="Import workflow" width="400">

2. Check and fix the n8n nodes.


    <img src="static/n8n-workflow.png" alt="n8n workflow" width="400">

3. Save and activate the workflow.

    <img src="static/n8n-save-workflow.png" alt="n8n activate" width="400">

4. Import the n8n_pipe.py to OWUI.

    <img src="static/n8n_pipe_in_owui.png" alt="import n8n to owui" width="400">

5. Expected Results.

    <img src="static/n8n-owui-demo.gif" alt = "Illustration of n8n workflow in OWUI" width="400">  



### Limitation

- does not support returning intermidiate steps while they are executing.