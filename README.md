# halite_bot
My Halite Bot submission.  Finish at Rank 5 before the finals, peaked at Rank 2.


__MyBot.py__

Contains the orchestration loginc between different subsystems. At one point, I was timing out frequently, so I decided to use the full duration of my early game seconds to evaluate paths rather than wait until I was time-crunched later. My raw BFS approach could take a lot of time, so I spawned a second thread at a couple of point to churn through the BFS of neutral but strength'd tiles. I tossed those in a persistent heap for the given tile so I could just pull off the top of that as I needed them. If the first path was no longer valid (i.e. ran into enemy or my territory or had 0 strength, I just used the next.

__Networking2.py__

Only interesting thing here is that at the start of every turn, while reading in the map, I created Moves for each tile that it shared with it's neighbors by type [friends, enemies, neutrals or empties] so that site.friends, had all the friendly locations and the direction for them to get to the current tile. Mostly this became a shortcut for counting different neighbor types later.

__Hlt2.py__

At some point I decided the locations should be singletons so that I could hash them to put them in a set and check for identity more easily. (This created a big memory leak for me at one point.)
Territory was the idea storing a player's total strength, production, edge tiles (frontier) and the neutral tiles next to them (fringe).
Trail was a path from a location


In Progress
