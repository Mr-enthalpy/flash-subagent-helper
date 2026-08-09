param([string]$Output = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml'))
. (Join-Path $PSScriptRoot 'common.ps1')

if (Test-Path -LiteralPath $Output) { throw "Refusing to overwrite existing local deployment: $Output" }
function Ask([string]$Prompt, [string]$Default) {
    $answer = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
    return $answer.Trim()
}

$codexHome = Ask 'Codex home' 'auto'
$ccrHome = Ask 'CCR home' 'auto'
$endpoint = Ask 'CCR local endpoint' 'http://127.0.0.1:3456/v1'
$family = Ask 'Worker model family' 'deepseek_flash'
$provider = Ask 'CCR provider id/display' '<USER_CONFIGURE>'
$route = Ask 'CCR route id' '<USER_CONFIGURE>'
$model = Ask 'Upstream model selector' '<USER_CONFIGURE>'
$identity = Ask 'Effective model identity (verify with provider)' '<USER_VERIFY>'
$profile = Ask 'Compatibility profile' 'deepseek_responses_v4'
$envName = Ask 'CCR client key environment variable NAME' 'CCR_CODEX_WORKER_KEY'
$present = -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($envName))

$content = @"
schema_version = 1

[deployment]
codex_home = "$codexHome"
ccr_home = "$ccrHome"
backup_root = "auto"

[worker]
model_family = "$family"
compatibility_profile = "$profile"
provider_id = "$provider"
model_selector = "$model"
effective_model_identity = "$identity"

[gateway]
local_base_url = "$endpoint"
client_key_env = "$envName"
route_id = "$route"

[deployment_policy]
allow_unverified_ccr = false
install_plugin = true
register_agents = true
"@
[IO.File]::WriteAllText($Output, $content.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
Write-Host "Created local, git-ignored deployment configuration: $Output"
Write-Host "Required environment variable present: $present (value not read or printed)"
Write-Host 'Configure the upstream provider credential in CCR outside this repository.'
