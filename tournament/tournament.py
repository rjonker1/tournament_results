#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    #return psycopg2.connect("dbname=tournament")
    return psycopg2.connect(database="tournament", user="postgres", password="bullseye", host="127.0.0.1", port="5432")


def deleteMatches():
    """Remove all the match records from the database."""
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('truncate matches')
        connection.commit()
    except psycopg2.DatabaseError, e:
        print 'An error occurred deleting matches %s' % e
    finally:
        if connection:
            connection.close()   


def deletePlayers():
    """Remove all the player records from the database."""
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('truncate players')
        connection.commit()
    except psycopg2.DatabaseError, e:
        print 'An error occurred deleting players %s' % e
    finally:
        if connection:
            connection.close()


def countPlayers():
    """Returns the number of players currently registered."""
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('select count(p.id) from players p;')
        result = cursor.fetchone()
        return result[0]
    except psycopg2.DatabaseError, e:
        print 'An error occurred getting a count of the players %s' % e
    finally:
        if connection:
            connection.close()

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('insert into players(fullname) values (%s) returning id;', (name,))
        playerId = cursor.fetchone()
        cursor.execute('insert into playerstandings(tournamentid, playerid, standing, wins, losses, ties, byes)values (1, %s,((select count(p.id) from players p)), 0, 0, 0, 0);', (playerId,))
        connection.commit()
    except psycopg2.DatabaseError, e:
        print 'An error occurred registering a player %s' % e
    finally:
        if connection:
            connection.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    connection = None
    standings = []
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('select p.id,p.fullname,(select count(mw.winnerplayerid) from matches mw where mw.winnerplayerid = p.id) wins, ((select count(mw.winnerplayerid)'
                       'from matches mw where mw.winnerplayerid = p.id) + (select count(mw.loserplayerid) from matches mw where mw.loserplayerid = p.id)) matches from players p;')
        rows = cursor.fetchall()
        for row in rows:
            standings.append(row)
        return standings
    except psycopg2.DatabaseError, e:
        print 'An error occurred getting a list of player standings %s' % e
    finally:
        if connection:
            connection.close()


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('insert into matches(tournamentid, resulttypeid, winnerplayerid, loserplayerid) VALUES (1,(select id from resulttypes where name = %(standard)s), '
                       '%(winner)s, %(loser)s);', {'winner' : winner,'loser' : loser, 'standard' : 'Standard'})
        connection.commit()
    except psycopg2.DatabaseError, e:
        print 'An error occurred reporting a match %s' % e
    finally:
        if connection:
            connection.close()
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """


