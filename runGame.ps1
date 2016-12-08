param(
        [Parameter(Mandatory=$false)][string]$seed
)

if (Test-Path bot.debug) {
	Remove-Item bot.debug
}
Remove-Item stats\*.stats -Force
$size = (20,25,30,35,40,45,50) | Get-Random
$size = (20,25, 30) | Get-Random
$player_count = (2,3,4,5,6) | Get-Random
$player_count = (2) | Get-Random

$players = New-Object System.Collections.ArrayList($null)
$players.add("python MyBot.py")
#$players.add("python MyBot.py")

for ($i=1; $i -lt $player_count; $i++)
{
  $players.add("python bots\ComboBot\MyBot.py")
}

if ($seed) {
	$seed="-s $seed"
}

$players
## "python MyBotCopy.py" "python 1.0-BlindwalkerBot-RandomInternalMovement.py	 "python 3.0-adimaria-MyBot.py" "python MyBotCopy.py" "python 3.0-adimaria-MyBot.py"
.\halite.exe -d "$size $size" $players $seed
Move-Item *.hlt replay.hlt -Force
Move-Item *.log error.log -Force
python printStats.py
#(python printStats.py | out-string -stream | sls -Pattern "(lineno|networking|hlt|MyBot)"| out-string -stream)
.\dist.ps1
