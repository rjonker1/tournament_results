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
        cursor.execute('truncate playerstandings')
        cursor.execute('truncate swisspairings')
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
        cursor.execute('update swisspairings set playerbid = (%s), paired = true where playeraid != 0 and paired = false and completed = false and matchid = 0 and playerbid = 0 RETURNING playerbid;', (playerId,))
        updatedPlayerId = cursor.fetchone()
        if updatedPlayerId == None:
            cursor.execute('insert into swisspairings(tournamentid, playeraid, playerbid, paired, completed, matchid) values (1,(%s),0, false, false, 0);', (playerId,))
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


def setNextPairing(player, cursor, connection):
    """Gets the next pairing for a player closest to their ranking.

    Args:
        player: the id number of the player to find a pairing for
        cursor: the current cursor object
        connection: the current connection object

    """
    availablePairings = []
    updated = 0
    cursor.execute('select playerId, standing from ((select playerId, standing from playerstandings where standing >= (select standing from playerstandings ps where ps.playerid = %(player)s) '
                   ' and playerid not in (%(player)s,(select winnerplayerid as playerid from matches where loserplayerid = %(player)s union select loserplayerid from matches where winnerplayerid = %(player)s)) '
                   ' order by standing limit 1) union (select playerId, standing from playerstandings where standing < (select standing from playerstandings ps where ps.playerid = %(player)s) '
                   ' and playerid not in (%(player)s,(select winnerplayerid as playerid from matches where loserplayerid = %(player)s union select loserplayerid from matches where winnerplayerid = %(player)s)) '
                   ' order by standing desc limit 1)) as ps order by standing', {'player' : player})
    rows = cursor.fetchall()          
    for row in rows:
        cursor.execute('select count(id) from swisspairings where completed = false and matchid = 0 and playerbid in(%(player)s,%(playerToPair)s) and playeraid in (%(player)s,%(playerToPair)s)'
                       , {'player' : player, 'playerToPair' : row[0]})
        isPaired = cursor.fetchone()
        if(isPaired[0] > 0):
            continue       
        
        while(updated == 0):            
            cursor.execute('update swisspairings set playerbid = %(player)s, paired = true where playeraid = %(playerToPair)s and completed = false and paired=false and matchid = 0 RETURNING playerbid;',
                           {'player' : player, 'playerToPair' : row[0]})
            updated = cursor.rowcount;
            cursor.execute('insert into swisspairings(tournamentid, playeraid, playerbid, paired, completed, matchid) values (1,(%s),0, false, false, 0);', (player,))            
            updated = cursor.rowcount;
        
    connection.commit()


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
                       '%(winner)s, %(loser)s) RETURNING id;', {'winner' : winner,'loser' : loser, 'standard' : 'Standard'})
        matchId = cursor.fetchone()
        cursor.execute('update swisspairings set completed = true, matchid = %(matchid)s where tournamentid = 1 and paired = true and (playerbid = %(winner)s or playeraid = %(winner)s) '
                       ' and (playerbid = %(loser)s or playeraid = %(loser)s) and matchid = 0',
                       {'winner' : winner,'loser' : loser, 'matchid' : matchId })
        cursor.execute('update playerstandings set wins = wins + 1 where playerId = (%s)', (winner,))
        cursor.execute('update playerstandings set losses = losses + 1 where playerId = (%s)', (loser,))
        cursor.execute('update playerstandings set standing = newstanding from ( '
                       ' select id, row_number() over (order by win_ratio desc) as newstanding from ( '
                       ' select distinct id, ((ps_b.wins  + ps_b.byes + (ps_b.ties/2)) / (case when (ps_b.losses + (ps_b.ties/2)) = 0 then 1 else (ps_b.losses + (ps_b.ties/2)) end)) win_ratio '
                       ' from playerstandings ps_b order by win_ratio desc ) as win_loss) as standings'
                       ' where standings.id = playerstandings.id')
        connection.commit()
        #Get available players to pair against
        setNextPairing(winner,cursor,connection)
        setNextPairing(loser,cursor,connection)
        #connection.commit()
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
    connection = None
    pairings = []
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('delete from swisspairings where playerbid = 0 and paired = false and completed = false and matchid = 0;')
        connection.commit()
        cursor.execute('select p.id id1 ,p.fullname name1, p2.id id2, p2.fullname name2 from swisspairings sp join players p on p.id = sp.playeraid join players p2 on p2.id = sp.playerbid '
                       ' where paired = true and completed = false and matchid = 0')
        rows = cursor.fetchall()
        for row in rows:
            pairings.append(row)
        return pairings
    except psycopg2.DatabaseError, e:
        print 'An error occurred getting next list of parings %s' % e
    finally:
        if connection:
            connection.close()


