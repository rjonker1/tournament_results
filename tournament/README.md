# Tournament Planner #

### Setup ###

### PostreSQL Database ###

*	Script file to setup the database is found in tournament.sql
*	Steps:
	*	Create a database called tournament in a PostreSQL database e.g.  CREATE DATABASE tournament;
	*	Use the command \i tournament.sql to import the whole file into psql at once. OR copy and paste each create table script to create the tables individuall
	*	Be sure to run the 'Seed Data' section at the end of the script file

### Executing the Code ###
*	In the tournament.py file, update the connect() function connection property to point to a database on your machine (i.e. update this: psycopg2.connect("dbname=tournament") )
*	Open the tournament_test.py file using python's shell. All tests should pass

### Additional Information ###
*	All functionalit can be found in the tournament.py file