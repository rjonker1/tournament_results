-- Database: tournament

-- DROP DATABASE tournament;

--CREATE DATABASE tournament


-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

--1. Drop Database if neccessary
--DROP DATABASE Tournaments  

--CREATE DATABASE tournament
--  WITH OWNER = postgres
--       ENCODING = 'UTF8'
--       TABLESPACE = pg_default
--       LC_COLLATE = 'English_United States.1252'
--       LC_CTYPE = 'English_United States.1252'
--       CONNECTION LIMIT = -1;


--1. Tournaments Table to store different tournaments 
create table Tournaments(
Id SERIAL primary key not null,
Name text not null
);
--2. Result Types to hold different result types e.g. win, loss, tie, bye
create table ResultTypes(
Type char(1) primary key not null,
Description text not null);

--3. Players table to hold information for each registered player
create table Players(
Id SERIAL primary key not null,
FullName text not null);

--4. Swiss Pairing table to store the pairings of players for each tournament
create table Pairings(
Id SERIAL primary key not null,
TournamentId int not null,
Draw int,
Round int,
PlayerId int DEFAULT 0 not null,
Paired boolean DEFAULT false not null,
Completed boolean DEFAULT false not null,
MatchId int DEFAULT 0 not null);

--5. Player standings to keep track of each players standing (or ranking) per tournament
create table PlayerStandings(
Id SERIAL primary key not null,
TournamentId int not null,
PlayerId int not null,
Standing int,
Wins int DEFAULT 0 not null,
Losses int DEFAULT 0 not null,
Ties int DEFAULT 0 not null,
Byes int DEFAULT 0 not null);

--6. Matches to hold information for each match per tournament (i.e. players, results, etc.)
create table Matches(
Id SERIAL primary key not null,
TournamentId int not null);

--7. Holds results for each match
create table MatchPlayers(
Id SERIAL primary key not null,
MatchId int not null,
PlayerId int not null,
Result char(1))

--Seed Data
--1. ResultTypes
insert into ResultTypes(Type,Description) values('W','Win');
insert into ResultTypes(Type,Description) values('T','Tie');
insert into ResultTypes(Type,Description) values('B','Bye');
insert into ResultTypes(Type,Description) values('L','Loss');

--2. Tournament
insert into Tournaments(name) values('Tournament A')





