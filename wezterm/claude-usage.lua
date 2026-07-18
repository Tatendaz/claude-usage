-- claude-usage for WezTerm: Claude quota in the right status area.
--
-- Install:
--   cp wezterm/claude-usage.lua ~/.config/wezterm/claude-usage.lua
-- then in ~/.config/wezterm/wezterm.lua:
--   require('claude-usage').setup()          -- defaults
--   -- or with options:
--   require('claude-usage').setup { bin = '/path/to/claude-usage', interval = 30 }
--
-- Note: setup() owns the right-status area via window:set_right_status(). If
-- you already render your own right status, call M.text() from your handler
-- instead of setup() and compose it yourself.

local wezterm = require 'wezterm'

local M = {}

local function default_bin()
  return (wezterm.home_dir or os.getenv 'HOME' or '') .. '/.local/bin/claude-usage'
end

local function refresh(bin, interval)
  local now = os.time()
  local last = wezterm.GLOBAL.claude_usage_at or 0
  if now - last < interval then
    return
  end
  wezterm.GLOBAL.claude_usage_at = now
  local ok, stdout = wezterm.run_child_process { bin }
  if ok and stdout and #stdout > 0 then
    wezterm.GLOBAL.claude_usage_text = stdout:gsub('%s+$', '')
  end
end

-- Latest cached status line (refreshing it at most every `interval` seconds).
function M.text(opts)
  opts = opts or {}
  refresh(opts.bin or default_bin(), opts.interval or 30)
  return wezterm.GLOBAL.claude_usage_text or '✳ …'
end

function M.setup(opts)
  opts = opts or {}
  wezterm.on('update-right-status', function(window, _)
    window:set_right_status(wezterm.format {
      { Text = (opts.prefix or '') .. M.text(opts) .. (opts.suffix or '  ') },
    })
  end)
end

return M
