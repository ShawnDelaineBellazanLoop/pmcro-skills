# PhaseMessage versus SendMessage

`PhaseMessage` is the portable protocol envelope. Claude Code's `SendMessage` is one possible host transport. A queue or MCP publish operation is another.

```text
PhaseMessage = what is sent
SendMessage  = Claude host transport
Queue        = durable delivery transport
TrailFrame   = durable verified state
```

For Claude, serialize the PhaseMessage as JSON inside `SendMessage`. For MAF, dispatch the same envelope through the host adapter. Do not make slash commands such as `/plugin:skill` the internal protocol.
