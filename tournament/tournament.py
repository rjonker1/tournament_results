#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection.

    This connection must point to a database on your machine

    """
    #return psycopg2.connect("dbname=tournament")
    return psycopg2.connect(database="tournament", user="postgres", password="bullseye", host="127.0.0.1", port="5432")


def deleteMatches():
    """Remove all the match records from the database."""
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute('delete from matchPlayers')
        cursor.execute('delete from matches')
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
        cursor.execute('delete from pairings')
        cursor.execute('delete from playerstandings')
        cursor.execute('delete from players')
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
        #insert a new player into the standings. A new player's standing will be max number of current players + 1 in the system
        cursor.execute('insert into playerstandings(tournamentid, playerid, standing, wins, losses, ties, byes)values (1, %s,((select count(p.id) from players p)), 0, 0, 0, 0);', (playerId,))

        #Find a pairing partner for the new player
        cursor.execute('insert into pairings(tournamentid,draw,round,playerid,paired,completed,matchid) values(1,case when (select count(id) from pairings p '
                       ' where p.paired = false and p.completed = false and p.matchid = 0) = 1 then (select max(p.draw) from pairings p) '
                       ' else (select (case when max(p.draw) isnull then 1 else (max(p.draw) + 1) end) from pairings p) end,1,(%s),false,false,0);', (playerId,))
        
        #check if players have been paired for this draw and round. If so, update the paired flag to true
        cursor.execute('update pairings set paired = true where id in (select pairings.id from pairings join pairings p on p.draw = pairings.draw '
                       ' group by pairings.id having count(pairings.draw) = 2) and paired=false;')
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
        cursor.execute('select p.id, p.fullname, (select count(mp.playerid) from matchplayers mp join resulttypes r on r.type = mp.result where mp.playerid = p.id and r.type = (%s)) wins, '
                       ' (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = p.id) matches from players p;', ('W'))
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
        
        #insert the match information
        cursor.execute('insert into matches(tournamentid)values (1)RETURNING id;')
        matchId = cursor.fetchone()
        cursor.execute('insert into matchplayers(matchid, playerid,result) values(%(match)s, %(player)s, (select type from resulttypes where type = %(result)s limit 1));'
                       ,{'player' : winner,'match' : matchId, 'result' : 'W' })
        cursor.execute('insert into matchplayers(matchid, playerid,result) values(%(match)s, %(player)s, (select type from resulttypes where type = %(result)s limit 1));'
                       ,{'player' : loser,'match' : matchId, 'result' : 'L' })
        
        #udate the pairings with the completed match
        cursor.execute('update pairings set completed = true, matchid = %(match)s where playerid = %(player)s and paired = true and matchid = 0 and round = (select max(round) from pairings);'
                       ,{'player' : winner,'match' : matchId})
        cursor.execute('update pairings set completed = true, matchid = %(match)s where playerid = %(player)s and paired = true and matchid = 0 and round = (select max(round) from pairings);'
                       ,{'player' : loser,'match' : matchId})
        
        #update the standings for the loser.
        #reset their wins, losses, etc. from their previous matches
        cursor.execute('update playerstandings set '
                       ' wins = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(wins)s), '
                       ' losses = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(losses)s), '
                       ' ties = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(ties)s), '
                       ' byes = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(byes)s) '
                       ' where playerid = %(player)s;'
                       ,{'player' : winner, 'wins' : 'W', 'losses' : 'L','ties' : 'T', 'byes' : 'B'})
        #update the standings for the loser.
        cursor.execute('update playerstandings set '
                       ' wins = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(wins)s), '
                       ' losses = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(losses)s), '
                       ' ties = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(ties)s), '
                       ' byes = (select count(m.id) from matches m join matchplayers mp on mp.matchid = m.id where mp.playerid = %(player)s and mp.result = %(byes)s) where playerid = %(player)s;'
                       ,{'player' : loser, 'wins' : 'W', 'losses' : 'L','ties' : 'T', 'byes' : 'B'})
        
        #update the player standings by calculating their win/loss ratio.
        #ties cound for half a win and half a loss
        #byes count as a win
        #win/loss = ((win + bye + tie)/2) / ((loss + (tie/2))
        cursor.execute('update playerstandings set standing = newstanding from ( '
                       ' select id, row_number() over (order by win_ratio desc) as newstanding from ( '
                       ' select distinct id, ((ps_b.wins  + ps_b.byes + (ps_b.ties/2)) / (case when (ps_b.losses + (ps_b.ties/2)) = 0 then 1 else (ps_b.losses + (ps_b.ties/2)) end)) win_ratio '
                       ' from playerstandings ps_b order by win_ratio desc ) as win_loss) as standings'
                       ' where standings.id = playerstandings.id')   
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
    connection = None
    pairings = []
    try:
        connection = connect()
        cursor = connection.cursor()
        #get a list of players and order by their standing. Then create a pairing for each player based on their standing matching it the next closest player
        cursor.execute('select ps.playerid from playerstandings ps order by ps.standing')
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute('insert into pairings(tournamentid,draw,round,playerid,paired,completed,matchid) values(1,case when (select count(id) from pairings p '
                           ' where p.paired = false and p.completed = false and p.matchid = 0) = 1 then (select max(p.draw) from pairings p) '
                           ' else (select (case when max(p.draw) isnull then 1 else (max(p.draw) + 1) end) from pairings p) end, '
                           ' (select (max(round) + 1) from pairings where completed = true and matchid > 0),(%s),false,false,0);', (row[0],))
            cursor.execute('update pairings set paired = true where id in (select pairings.id from pairings join pairings p on p.draw = pairings.draw '
                           ' group by pairings.id having count(pairings.draw) = 2) and paired=false;')
            connection.commit()
        #pivot the results pairings to the id(s) and names of each paired plaer
        cursor.execute('select max(case when rownumber = 1 then id end) as "id1",max(case when rownumber = 1 then fullname end) as "name1", '
                       ' max(case when rownumber = 2 then id end) as "id2",max(case when rownumber = 2 then fullname end) as "name2" from '
                       ' (select pl.id, pl.fullname, p.draw, row_number() over (partition by p.draw order by p.draw asc) as rownumber from players pl '
                       ' join pairings p on p.playerid = pl.id where p.paired = true and completed = false and matchid = 0) p group by draw order by draw')
        rows = cursor.fetchall()
        for row in rows:
            pairings.append(row)
        return pairings
    except psycopg2.DatabaseError, e:
        print 'An error occurred getting next list of parings %s' % e
    finally:
        if connection:
            connection.close()


