# rps-conversational-agent


user input 
    |
[Node 1: Intent Understanding]
- parse what the user meant
- extract the move attempt
    |
[Node 2: Validation]
- check if move clear/unclear/invalid
- bomb constraints and game state
    |
[Node 3: Game Logic]
- determine who won the round
- update state -> bomb used or not, score
    |
[Node 4: Resonse Generation]
- format feedback for user
- show round results
- continue or end game