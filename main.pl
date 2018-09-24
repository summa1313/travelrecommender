
%
% EECS 371
% Term Project
% Travel Recommender
%
% Uses knowledge base 'kb.pl'
% 
% In prolog console:
%    to load file: "[main]." 
%    to execute  : "main."
%

%
% include Knowledge base
%
:- consult(kb),
  write('Loaded'), 
  nl.

% Main function
main :-
  write('Travel Recommender'), nl,
  write('Every answer must be followed by a dot (.)'), nl,

  reset_answers,                              % reset answers
  ask(distance, 'How far can you travel?', _), % ask about distance

  setof(X,find_place(X),Countries),     % find countries for current filters
  %write('start with '), write(Countries),
  ask_user(Countries, Out, 5),          % ask more questions, 5 questions max

  print_results(Out),                   % print countries list with descriptions
  nl.

% Store user answers to be able to track his progress
:- dynamic user_answer/1.

%
% find places that satisfy current filters
%
search_place([], _).
search_place([Answer|Rest], Country) :-
  has(Country,_,Answer),
  search_place(Rest, Country).
find_place(Place) :-
  setof(X, user_answer(X), Answers), % get user answers
  search_place(Answers, Place).
find_place(Place) :-
  \+ setof(X, user_answer(X), _), % no user answers yet
  has(Place, _, _).

%
% Get list of active filters (user answers)
%
get_active_filters(Filters) :-  
  setof(X,user_answer(X),Filters).
get_active_filters(Filters) :-  
  \+ setof(X,user_answer(X),Filters),
  Filters = [].

%
% Ask about options
%
ask_user([A], [A], _).   % we are done when one country left
ask_user(A, A, 0).   % we are done when reached 
ask_user(Countries, Out, QuestionIndex) :-  
  %write('Countries: '), write(Countries), nl,
  get_active_filters(ActiveFilters),
  %write('ActiveFilters: '), write(ActiveFilters), nl,
  write('Choose filters:'), nl,
  setof(Answer,Country^Question^(has(Country,Question,Answer), member(Country, Countries), \+ member(Answer, ActiveFilters), not(Question = distance)), L),  % query all attributes that match filtered countries!
  print_answers(L, 0),
  read(Index),                                % read user input
  parse(Index, L, Response),                  % Response = Choices[Index] 
  asserta(user_answer(Response)),             % assert new fact (save user response)
  setof(X,find_place(X),UpdatedCountries),
  NextIndex is QuestionIndex - 1,
  ask_user(UpdatedCountries, Out, NextIndex).            % continue asking questions with new set of countries

%
% Print results
%
print_results([]) :-
  write('\n\nWe couldn\'t find a destination for your criterias. Try again.\n\n').

print_results(Places) :-
  get_active_filters(ActiveFilters),
  write('\n\nYour requests: '), write(ActiveFilters),
  write('\n\nWe suggest:\n\n'),
  print_places(0, Places).

print_places(_,[]).            % terminate if list is empty
print_places(5,[_|_]).        % handle max results limit
print_places(Index,[Place|Rest]) :-
  NextIndex is Index + 1,
  write('------------| '), write(NextIndex), write('. '), write(Place), write(' |------------'), nl,
  capital(Place, C),                    % find capital into variable C
  write('Capital: '), write(C), nl,
  distance(Place, K),                   % find distance into variable K
  write('Distance: '), write(K), nl,
  description(Place, D),                % find description into variable D  
  write(D), nl, nl,  
  print_places(NextIndex,Rest).         % print next place from the list (recursive)


%
% Clear user answers
%
reset_answers([]).
reset_answers([X|Rest]) :-
  retract(user_answer(X)),
  reset_answers(Rest).
reset_answers :-
  findall(X,user_answer(X),L),
  reset_answers(L).

%
% Ask single question
%
ask(Q, Text, Answer) :-
  setof(X,Country^(has(Country,Q,X)),Choices),    % get list of answers for question from the list
  write(Text),nl,                                % print question
  print_answers(Choices, 0),                        % print list  of answers starting from index 0
  read(Index),                                % read user input
  parse(Index, Choices, Response),            % Response = Choices[Index] 
  asserta(user_answer(Response)),             % assert new fact
  Response = Answer.          

%
% Print a nicely formatted list of answers
% [First|Rest] is the Choices list, Index is the index of First in Choices
%
print_answers([], _).                               % terminate for empty list
print_answers([First|Rest], Index) :-
  write(Index), write(' '), write(First), nl,  % print option
  NextIndex is Index + 1,                      % increment Index
  print_answers(Rest, NextIndex).                    % recurse with the rest of the list

%
% Parses an Index and returns a Response representing the "Indexth" element in
% Choices (the [First|Rest] list)
%
parse(0, [First|_], First).
parse(Index, [_|Rest], Response) :-
  Index > 0,
  NextIndex is Index - 1,
  parse(NextIndex, Rest, Response).



% functions to extract capital and description from dbpedia
capital(Country, Capital) :-
  queryCapital(Country, Capital).
capital(Country, Capital) :-
  \+ queryCapital(Country, Capital),
  Capital = "".

description(Country, Description) :-
  queryDescription(Country, Description).
description(Country, Description) :-
  \+ queryDescription(Country, Description),
  Description = "".

%
% SPARQL
%
queryCapital(Country, Capital) :-   %% e.g. Country = '"Canada"'
  use_module(library(semweb/sparql_client)),
  atomic_list_concat( [ 'SELECT ?capital_name WHERE {
           {?country rdfs:label "', Country, '"@en}
           {?country a dbo:Country }
           {?country dbo:capital ?capital}
           {?capital rdfs:label ?capital_name}
            FILTER (lang(?capital_name) = "en")
          }'], Query),
  sparql_query(Query, Row, [ host('dbpedia.org'), path('/sparql/')] ),
  queryValue(Row, Capital).

queryDescription(Country, Description) :-   %% e.g. Country = '"Canada"'
  use_module(library(semweb/sparql_client)),
  atomic_list_concat( [ 'SELECT ?descr WHERE { {?name rdfs:label "Tourism in ', Country, '"@en } '], A),
  atomic_list_concat( [ 'UNION {?name rdfs:label "Tourism in the ', Country, '"@en } 
                        ?name dbo:abstract ?descr
                        FILTER (lang(?descr) = "en") }'], B),
  atomic_list_concat( [ A, B], Query),
  sparql_query(Query, Row, [ host('dbpedia.org'), path('/sparql/')] ),
  queryValue(Row, Description).

% extract value from SPARQL row
queryValue(Row,Value) :-  
  row(literal(lang(en, Value))) = Row.

%
% test for debugging purposes
%
test() :-
  reset_answers,
  asserta(user_answer(water, 'snorkel')),
  asserta(user_answer(cultural, 'doesn\'t matter')),
  asserta(user_answer(forest, 'doesn\'t matter')),
  asserta(user_answer(mountain, 'doesn\'t matter')),
  asserta(user_answer(distance, 'long haul')),
  asserta(user_answer(park, 'safari')),
  asserta(user_answer(type, 'water')),  
  findall(A,user_answer(A,_),Q),  % get list of questions
  write(Q),nl,
  findall(X,find_place(X,Q),Places),         % find all possible places according to criterias
  %write(Places), nl,
  print_results(Places).
