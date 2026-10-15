# C5 review agreement

16 obligations of deliver-feature (before and after the contract fixes); 3 do not hold in the reference review.

| Reviewer | Answered | Accuracy | Gaps found | False alarms | Uncovered named right | Kappa vs reference |
|---|---|---|---|---|---|---|
| anthropic (claude-opus-5-5) | 16 | 0.875 | 3/3 | 2/13 | 3/3 | 0.673 |
| openai (gpt-6-astra) | 16 | 0.75 | 3/3 | 4/13 | 3/3 | 0.458 |
| google (gemini-3.1-pro-preview) | 16 | 0.875 | 3/3 | 2/13 | 3/3 | 0.673 |
| human R1 | 16 | 0.812 | 3/3 | 3/13 | 3/3 | 0.556 |

| Pair | Kappa |
|---|---|
| anthropic (claude-opus-5-5) vs openai (gpt-6-astra) | 0.738 |
| anthropic (claude-opus-5-5) vs google (gemini-3.1-pro-preview) | 1.0 |
| anthropic (claude-opus-5-5) vs human R1 | 0.862 |
| openai (gpt-6-astra) vs google (gemini-3.1-pro-preview) | 0.738 |
| openai (gpt-6-astra) vs human R1 | 0.613 |
| google (gemini-3.1-pro-preview) vs human R1 | 0.862 |
