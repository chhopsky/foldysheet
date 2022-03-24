### THE FOLDY SHEET

The foldy sheet is a physical implementation of a binary tree representing the full set of every possibility of the outcome of a regular LCS season, and is used to determine who's made playoffs, who hasn't, and how many scenarios in which team X makes it.

This program works for all riot leagues supported by Panda, which is most of them.

Requirements: Python 3.8, pipenv

HOW TO USE:
1. You'll need to get a key from PandaScore so you can get the league data: https://app.pandascore.co/signup
2. Put it in config.py, and set the slug for the league you want to evaluate.
3. pipenv shell
4. Run python foldysheet.py to generate every possible result.
5. Run can_they_make_it.py, then either 'locked', 'eliminated', or 'maybe'.

Locked and eliminated are self explanatory. Maybe will tell you the number of scenarios in which a team *can* make it. Since every region has its own tiebreaker rules, this does *not* tell you how ties are solved. A scenario in which a team is tied will count both as a possibility and tell you who's tied. You can then apply your region's head to head rules to fix it.

NA tiebreaker rules are included but optional to implement - run your possibility through `tiebreaker(possibility)` to apply them.

Playoff lock is manually set to 6th place, because I wrote this primarily for LCS. Technically it can work on any esport that deals with BO1s and is on pandascore, it also works for BO3s, but playoff elimination rules may be different based on win-scores (2-0 vs 2-1) so YMMV.

Any questions, hit me up @chhopsky on twitter.

### LICENSING INFORMATION

This program comes with absolutely no warranties or guarantees of any kind. It is for personal, non-commercial use only. If you use this program for commercial purposes, including but not limited to broadcast, written articles, social media, or videos, you require a license. Unlicensed commercial use will result in legal remedies being aggressively pursued.

Pricing varies depending on company and use. Contact me on twitter or via email to obtain a commercial license.
