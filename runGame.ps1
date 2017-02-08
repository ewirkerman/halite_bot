param(
        [Parameter(Mandatory=$false)][string]$seed
)

if (Test-Path bot.debug) {
	Remove-Item bot.debug
}

.\dist.ps1

Remove-Item stats\*.stats -Force
$size = (20,25,25,30,30,30,35,35,35,40,40,40,45,45,50) | Get-Random
$size = (50) | Get-Random
$player_count = (2,2,2,2,2,3,3,3,3,4,4,4,5,5,6) | Get-Random
$player_count = (2) | Get-Random


$myBot = "python -m memory_profiler MyBot.py"
$myBot = "python bots\MyBot\MyBot.py"
$myBot = "python MyBot.py"

$players = New-Object System.Collections.ArrayList($null)
$players.add($myBot)

$opponents = New-Object System.Collections.ArrayList($null)
$opponents.add("python bots\ComboBot\MyBot.py")
$opponents.add("python bots\BreachBot\MyBot.py")
# $opponents.add("python bots\MyBot\MyBot.py")
# $opponents.add("python bots\PypyBot\MyBot.py")





for ($i=1; $i -lt $player_count; $i++)
{
  $opponent = $opponents | Get-Random
  $players.add($opponent)
}

if ($seed) {
	$seed="-s $seed"
}


$children = Get-ChildItem [1-9]*.hlt

$players
.\halite.exe -d "$size $size" $players $seed 

Remove-Item $children -Force

Move-Item *.log error.log -Force
# python printStats.py
#(python printStats.py | out-string -stream | sls -Pattern "(lineno|networking|hlt|MyBot)"| out-string -stream)

