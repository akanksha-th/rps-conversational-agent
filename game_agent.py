from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Literal
import random
from llm import call_llm

class GameState(TypedDict):
    # Game State
    round_number: int
    best_of: int = 5
    user_bomb_used: bool
    bot_bomb_used: bool
    user_score: int
    bot_score: int

    # Current Round
    user_input: str
    user_move: str | None
    bot_move: str

    # Evaluation
    move_status: Literal["valid", "invalid", "unclear"]
    move_status_reason: str     # Explanation for predicted move_status
    round_winner: str | None    # user / bot / draw

    # Output
    round_feedback: str
    game_over: bool
    final_winner: str | None

    
def intent_node(state: GameState) -> GameState:
    """uses LLM to understand the user intended move"""
    user_input = state["user_input"]

    prompt = f"""
You are parsing a user's move in Rock-Paper-Scissors-Bomb game.

Valid moves: rock, paper, scissors, bomb

User said: {user_input}

Extract the intended move. Handle typos, variations and casual language.
Examples:
- "rock" / "rok" / "r" → {{"move": "rock", "confidence": "high"}}
- "paper" / "p" → {{"move": "paper", "confidence": "high"}}
- unclear → {{"move": null, "confidence": "low"}}

Return JSON: 
{{
    'move': 'rock' | 'paper' | 'scissors' | 'bomb' | 'null',
    'confidence': 'high' | 'medium' | 'low'
}}

CRITICAL: Return ONLY a JSON object with NO markdown, NO explanation.
If unclear, set move to null.
    """

    response = call_llm(prompt)

    if response:
        state["user_move"] = response.get("move")
    else:
        state["user_move"] = None

    return state

def judge_node(state: GameState) -> GameState:
    """applies game rules using prompt-driven learning"""
    base_moves = ["rock", "paper", "scissors"]
    available_moves = (
        base_moves if state["bot_bomb_used"]
        else base_moves + ["bomb"]
    )
    
    state["bot_move"] = random.choice(available_moves)
    if state["bot_move"] == "bomb":
        state["bot_bomb_used"] = True

    prompt = f"""
You are the judge for Rock-paper-scissors-bomb.

RULES:
1. valid moves: rock, paper, scissors, bomb.
2. bomb beats everything except bomb. Bomb vs Bomb = draw.
3. standard rps: rock > scissors, paper > rock, scissors > paper.
4. invalid or unclear moves = automatic round loss.
5. bomb can be used ONLY ONCE by each player.

GAME STATE: 
- Round: {state["round_number"]}
- User's bomb already used: {state["user_bomb_used"]}
- Bot's bomb already used: {state["bot_bomb_used"]}

THIS ROUND:
- User move: {state["user_move"]}
- Bot move: {state["bot_move"]}

Evaluate and return ONLY valid JSON:
{{
    "move_status": "valid" | "invalid" | "unclear",
    "reason": "brief explanation in 1 sentence",
    "round_winner": "user" | "bot" | "draw" | "null"
}}

if user is null, then status: "unclear", winner: "null"
if user tries bomb when he has already used it, then status: "invalid", winner: "null"

CRITICAL: Return ONLY a JSON object with NO markdown, NO explanation.
Strictly apply mentioned game rules.
"""
    result = call_llm(prompt)
    if result:
        state["move_status"] = result.get("move_status")
        state["move_status_reason"] = result.get("reason", "")
        state["round_winner"] = result.get("round_winner")

        if state["round_winner"] == "user":
            state["user_score"] += 1
        elif state["round_winner"] == "bot":
            state["bot_score"] += 1
        
        if state["user_move"] == "bomb" and state["move_status"] == "valid":
            state["user_bomb_used"] = True

    return state

def response_node(state: GameState) -> GameState:
    """produce structured, user-facing explanation"""
    prompt = f"""
ROUND: {state["round_number"]}
USER MOVE: {state["user_move"]} ({state["move_status"]})
BOT MOVE: {state["bot_move"]}
REASON: {state["move_status_reason"]}
WINNER: {state["final_winner"]}

SCORE:
- User: {state["user_score"]} wins
- Bot: {state["bot_score"]} wins

Create feedback, stating:
1. what happened, clearly
2. why certain moves were invalid or unclear
3. current score
4. round number

Keep it concise.
"""
    feedback = call_llm(prompt)
    state["round_feedback"] = feedback or "Round Complete"

    rounds_to_win = (state["best_of"] // 2) + 1
    
    if state["user_score"] >= rounds_to_win:
        state["game_over"] = True
        state["final_winner"] = "user"
    elif state["bot_score"] >= rounds_to_win:
        state["game_over"] = True
        state["final_winner"] = "bot"

    state["round_number"] += 1
    state["best_of"] -= 1

    if state["best_of"] == 0:
        state["game_over"] = True
    return state

def should_continue(state: GameState) -> str:
    """decide if the game continues or ends"""
    if state["game_over"]:
        return "end"
    return "continue" 


def build_graph():
    graph = StateGraph(GameState)

    graph.add_node("intent", intent_node)
    graph.add_node("judge", judge_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "intent")
    graph.add_edge("intent", "judge")
    graph.add_edge("judge", "response")
    graph.add_conditional_edges(
        "response",
        should_continue,
        {
            "continue": "intent",
            "end": END
        }
    )

    return graph.compile()


if __name__ == "__main__":
    graph = build_graph()
    best_of = 3

    initial_state = {
        "round_number": 1,
        "best_of": 5,
        "user_bomb_used": False,
        "bot_bomb_used": False,
        "user_score": 0,
        "bot_score": 0,
        "user_input": "",
        "user_move": None,
        "bot_move": "",
        "move_status": "valid",
        "move_status_reason": "",
        "round_winner": None,
        "round_feedback": "",
        "game_over": False,
        "final_winner": None
    }

    state = initial_state

    while not state["game_over"]:
        state["user_input"] = input(f"\nRound {state["round_number"]} - What's your move?: ")
        state = graph.invoke(state)
        print(state["round_feedback"])

    print(f"\n{'='*50}")
    print("GAME OVER\n")
    print(f"Winner: {state["final_winner"].upper()}")
    print(f"Final Score - User: {state["user_score"]}, Bot: {state["bot_score"]}")
    print(f"\n{'='*50}")
