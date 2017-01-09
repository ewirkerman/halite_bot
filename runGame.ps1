param(
        [Parameter(Mandatory=$false)][string]$seed
)

if (Test-Path bot.debug) {
	Remove-Item bot.debug
}
Remove-Item stats\*.stats -Force
$size = (20,25,30,35,40,45,50) | Get-Random
$size = (50) | Get-Random
$player_count = (2,3,4,5) | Get-Random
$player_count = (2) | Get-Random

$players = New-Object System.Collections.ArrayList($null)

.\dist.ps1
$players.add("python bots\MyBot\MyBot.py")
# $players.add("python MyBot.py")

for ($i=1; $i -lt $player_count; $i++)
{
  $players.add("python bots\ComboBot\MyBot.py")
}

if ($seed) {
	$seed="-s $seed"
}


$children = Get-ChildItem [1-9]*.hlt

$players
.\halite.exe -d "$size $size" $players $seed

Remove-Item $children -Force

Move-Item *.log error.log -Force
python printStats.py
#(python printStats.py | out-string -stream | sls -Pattern "(lineno|networking|hlt|MyBot)"| out-string -stream)

