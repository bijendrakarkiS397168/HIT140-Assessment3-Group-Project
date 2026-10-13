### Context

I just wanted a semi-definitive list of international football matches, that was easy to read and that was not available. So I took it upon myself to collect it for my own use. I'd better put it out there.

### Content

This data set contains the results of 49,459 international football matches from the first official match in 1872 up to 2024. Matches can be from the FIFA World Cup, the FIFI Wild Cup or regular friendly matches. The matches are pure full internationals and the data is not based on Olympic Games or games that involved at least one of the team as a B-team of the country or U-23 or a team that was selected from a league.

The following columns are included in results.csv:

A string representing the match's date.-   `date` - the date of the match.
-   `home_team` - home team (name)
-   away_team – the name of the away team
full time home score (excluding penalty shoot-outs)
- away_score - full-time away team score (excluding penalty-shootouts)
-   `tournament` - the name of the tournament
The name of the city/town/administrative unit in which the match was played.
-   `country` - name of country of match
- neutral – boolean column that is true if the match was played on neutral ground, false otherwise

`shootouts.csv` includes the following columns:

-   `date` - date of the match
The name of the home team.The name of the home team (required).
-   `away_team` - name of the away team
-   `winner` - winner of the penalty-shootout
-   `first_shooter` - the team which was shot at first in the shootout

The `goalscorers.csv` file contains the following fields:

-   `date` - date of the match
-   `home_team` – name of the home team
-   `away_team` - Name of the away team.
-   `score` - score of the goal (a number)
-   `scorer` - name of the player that scored the goal
-   `own_goal` - if the goal was an own-goal or not
-   `penalty` - was the goal a penalty?

Note on team and country names: Current name of the team has been used for home and away teams. In this Dataset, for example, when in 1882 a team known as Ireland played England, it is listed as Northern Ireland as the current team of Northern Ireland is the descendant of the 1882 Ireland team. This is done to simplify the tracking of teams' history and statistics.

The names of the countries are used according to the name of the country in the time of the match. So when Ghana played in Accra, Gold Coast in the 1950s, even though the names of the home team and the country don't match, it was a home match for Ghana. The neutral column reads "FALSE" for those games, which means it was not played at a neutral venue.

### Acknowledgements

It is collected from a variety of sources, such as but not limited to Wikipedia and rsssf.com, and the websites of individual football associations.

### Inspiration

Here are some suggestions on how to investigate the data:

-   Who is the worst team of all time
-   The key events in the evolution of soccer clubs from the mid-20th century to the present
-   What trends have there been in international football throughout the ages - home advantage, total goals scored, distribution of teams' strength etc
What can be learned from football fixtures about geopolitics – has the number of countries changed, do certain teams enjoy playing each other?
Which countries have the fewest games in which they are not playing in their own country?
-   What is the impact on a country's chances in the tournament if they host a large tournament?
-   Who are the most active teams in playing friendlies and friendly tournaments and are they helped or hindered -

The world's your oyster, my friend.

### Contribute
