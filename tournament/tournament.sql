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

--1. Tournaments Table to store different tournaments 
create table Tournaments(
Id SERIAL primary key not null,
Name text not null
);
--2. Result Types to hold different result types e.g. win, loss, tie, bye
create table ResultTypes(
Id SERIAL primary key not null,
Name text not null);

--3. Players table to hold information for each registered player
create table Players(
Id SERIAL primary key not null,
FullName text not null);

--4. Swiss Pairing table to store the pairings of players for each tournament
create table SwissPairings(
Id SERIAL primary key not null,
TournamentId int not null,
PlayerAId int not null,
PlayerBId int not null);

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
TournamentId int not null,
PairingId int not null,
ResultTypeId int not null,
WinnerPlayerId int,
LoserPlayerId int);


--create view OpponentMatchWins(
--Id SERIAL primary key not null,
--PlayerId int not null,
--OppenentId int not null);

--Seed Data
--1. ResultTypes
insert into ResultTypes(name) values('Win');
insert into ResultTypes(name) values('Loss');
insert into ResultTypes(name) values('Tie');
insert into ResultTypes(name) values('Bye');

--2. Tournament
insert into Tournaments(name) values('Tournament A')





