param(
        [Parameter(Mandatory=$false)][string]$seed
)

if (Test-Path bot.debug) {
	Remove-Item bot.debug
}
Remove-Item stats\*.stats -Force
$size = (20,25,30,35,40,45,50) | Get-Random
$size = (35) | Get-Random
$player_count = (2,3,4,5) | Get-Random
$player_count = (2) | Get-Random

$players = New-Object System.Collections.ArrayList($null)

# $players.add("python bots\MyBot\MyBot.py")
$players.add("python MyBot.py")

for ($i=1; $i -lt $player_count; $i++)
{
  $players.add("python bots\ComboBot\MyBot.py")
}

if ($seed) {
	$seed="-s $seed"
}

Remove-Item *.hlt -Force

$players
.\halite.exe -d "$size $size" $players $seed


Move-Item *.log error.log -Force
python printStats.py
#(python printStats.py | out-string -stream | sls -Pattern "(lineno|networking|hlt|MyBot)"| out-string -stream)
.\dist.ps1
