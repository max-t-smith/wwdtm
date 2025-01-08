-- I included this in the Repo so those interested can get more info on how the DB is structured

USE wwdtm_app;

SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS limericks;
DROP TABLE IF EXISTS fill_in_blanks;
DROP TABLE IF EXISTS bluff_the_listeners;
DROP TABLE IF EXISTS quotes;

SET FOREIGN_KEY_CHECKS=1;


CREATE TABLE games
(
    gameid       int not null AUTO_INCREMENT,
    status       varchar(64) not null,
    PRIMARY KEY (gameid)
);

CREATE TABLE players
(
    playerid    int not null AUTO_INCREMENT,
    playername  varchar(128),
    PRIMARY KEY (playerid)
);

CREATE TABLE scores
(
    scoreid     int not null AUTO_INCREMENT,
    playerid    int not null,
    gameid      int not null,
    score       float not null,
    PRIMARY KEY (scoreid),
    FOREIGN KEY (playerid) REFERENCES players(playerid),
    FOREIGN KEY (gameid) REFERENCES games(gameid)
);

CREATE TABLE limericks
(
    limerickid      int not null AUTO_INCREMENT,
    gameid          int not null,
    line1           varchar(1000),
    line2           varchar(1000),
    line3           varchar(1000),
    line4           varchar(1000),
    line5           varchar(1000),
    answer          varchar(1000),
    info            varchar(10000),
    PRIMARY KEY (limerickid),
    FOREIGN KEY (gameid) REFERENCES games(gameid)

);

CREATE TABLE fill_in_blanks
(
    questionid      int not null AUTO_INCREMENT,
    gameid          int not null,
    question        varchar(1000),
    answer          varchar(1000),
    PRIMARY KEY (questionid),
    FOREIGN KEY (gameid) REFERENCES games(gameid)

);

CREATE TABLE bluff_the_listeners
(

    storiesid   int not null AUTO_INCREMENT,
    gameid      int not null,
    intro       varchar(1000),
    story1      varchar(5000),
    story2      varchar(5000),
    fake        varchar(5000),
    PRIMARY KEY(storiesid),
    FOREIGN KEY (gameid) REFERENCES games(gameid)

);

CREATE TABLE quotes
(

    quoteid     int not null AUTO_INCREMENT,
    gameid      int not null,
    quote       varchar(1000),
    question    varchar(1000),
    answer      varchar(1000),
    info        varchar(10000),
    PRIMARY KEY (quoteid),
    FOREIGN KEY (gameid) REFERENCES games(gameid)

);









