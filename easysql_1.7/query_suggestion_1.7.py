from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from prompt_toolkit import PromptSession
from prompt_toolkit.validation import Validator
from prompt_toolkit.key_binding import KeyBindings

import re
import shutil
import os

from serverConnect import serverConnect
from check_syntax import checkSyntax
from score_manage import score_manage
from getChracter import getChracter
from showOutput import showOutput


TABLE_USED:list[str]=[]


# Get terminal width dynamically
terminal_width = shutil.get_terminal_size().columns


def remove_duplicates(List):
    seen = set()
    return [x for x in List if not (x in seen or seen.add(x))]

def is_keywords(token:str)->bool:
    #if token is belongs from sql reserv keywords then retun true else flase
    sql_keywords = {
    "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "BACKUP", "BETWEEN", "CASE", "CHECK", "COLUMN",
    "CONSTRAINT", "CREATE", "DATABASE", "DEFAULT", "DELETE", "DESC", "DISTINCT", "DROP", "EXEC", "EXISTS", "FOREIGN",
    "FROM", "FULL", "GROUP", "HAVING", "IN", "INDEX", "INNER", "INSERT", "INTO", "IS", "JOIN", "KEY", "LEFT", "LIKE",
    "LIMIT", "NOT", "NULL", "OR", "ORDER", "OUTER", "PRIMARY", "PROCEDURE", "RIGHT", "ROWNUM", "SELECT", "SET", 
    "TABLE", "TOP", "TRUNCATE", "UNION", "UNIQUE", "UPDATE", "VALUES", "VIEW", "WHERE"}

    token = token.strip()
    if len(token)>1 and token[0]=='(':
        #token = re.sub(r'(', '' ,token)
        token = token[1:]
        #if token == 'SELECT':
        #    print(token,"is presnt")
        ...
    
    return True if token in sql_keywords else False
    ...


def read_queries(file_path:str)->list[str]:
    queries=""
    if os.path.exists(file_path):
        #read the text file 
        with open(file_path, 'r') as f:
            text = f.read()
        #Then remove all redundent symbols
        pattern = r'[;$#`\--]'
        text = re.sub(pattern, '', text)
        #then finaly break them all small token based on the space
        queries = [query.strip().upper() for query in text.split("\n") if query.strip()]
    return queries if queries else ""

def tokenize_queries(queries:list[str])->list[list[str]]:
    #Tokenizes queries into lists of words
    tokenized_queries = []
    for query in queries:
        tokens = query.split()
        tokenized_queries.append(tokens)
    #print(tokenized_queries)
    return tokenized_queries if tokenized_queries else []

def is_placeholder(word:str)->bool:
    #Checks if a word is a placeholder (like [field1], [table], [value])
    return bool(re.match(r'\[.*?\]', word))  # Matches words enclosed in []

def is_field_required(word:str)->str:
    ...

def suggestActualTable(suggestions:list[str],tables:list[str])->list[str]:
    #print(f"in the function {suggestions} {tables}")
    if '[TABLE]' in suggestions:
        #print(f"in the function {suggestions} {tables}")
        suggestions.extend(tables)
        suggestions.remove('[TABLE]')
    return suggestions if suggestions else []
    ...

def suggestActualFields(suggestions:list[str],fields:dict[str:list[str]])->list[str]:
    #print(f"in the function {suggestions} {fields}")
    if '[FIELD]' in suggestions:
        #print('fileds are added')
        #print(f"in the function {suggestions} {fields}")
        for table, _fields in fields.items():
            suggestions.extend(_fields)
        suggestions.remove('[FIELD]')
    return suggestions if suggestions else []
    ...


def getComparisonOperators(suggestions:list[str])->list[str]:
    List = ['=','<','>','<>','<=','>=']
    if '[COMPARISON]' in suggestions:
        suggestions.extend(List)
        suggestions.remove('[COMPARISON]')
    return suggestions
    ...

def getArithmeticOperators(suggestions:list[str])->list[str]:
    List = ['+','-','*','/']
    if '[ARITHMETIC]' in suggestions:
        suggestions.extend(List)
        suggestions.remove('[ARITHMETIC]')
    return suggestions
    ...


def getLogicalOperators(suggestions:list[str])->list[str]:
    List = ['AND','OR','NOT']
    if '[LOGICAL]' in suggestions:
        suggestions.extend(List)
        suggestions.remove('[LOGICAL]')
    return suggestions
    ...


def suggestSubqueries(suggestions:list[str])->list[str]:
    if any(bool(re.search(r'\[VALUE\]\S*', word)) or word == 'VALUES' or bool(re.search(r'\[FIELD\]\S*', word)) or bool(re.search(r'\[TABLE\]\S*', word)) for word in suggestions):
    #if any(re.search(r'\[VALUE\]\S*', word) or word == 'VALUES' or re.search(r'\[FIELD\]\S*', word) or re.search(r'\[TABLE\]\S*', word) for word in suggestions):
        #then here select subquery can be add
        suggestions.append('( SELECT')
    return suggestions
    ...


def remove_immidiate_used_token_from_suggestion(completed_tokens:list[str],suggestions:list[str])->list[str]:
    #print(f"completed tokens : {completed_tokens}")
    if completed_tokens and completed_tokens[-1] in suggestions:
        suggestions.remove(completed_tokens[-1])
    return suggestions if suggestions else []
    ...

#retuns true even the variables like r'\[.*?\]' present in the query
#return false if other tokens is not matched
def is_token_matched_without_variables(tokens:list[str],completed_tokens:list[str])->bool:
    index = 0
    # print(tokens[0])
    for token in tokens[:len(completed_tokens)]:
        if is_placeholder(token) and not is_keywords(completed_tokens[index].upper()):
            index+=1
            #print(">>>",completed_tokens[index-1].upper())
            continue
        if token != completed_tokens[index].upper():
            return False
        index+=1
    return True

# def is_previous_tokens_matched_to_tokenlist(tokens:list[str],completed_tokens:list[str])->bool:
#     index = 0
#     for token in tokens[:len(completed_tokens)]:
#         if token != completed_tokens[index].upper():
#         ...
#     ...

# def count_consecutive_tokens_ending_with_comma_from_end(tokens: list[str]) -> int:
#     if not tokens:  # Handle empty list case
#         return 0

#     if not tokens[-1].endswith(','):  # Check if the last token does not end with a comma
#         return 0

#     count = 0
#     for token in reversed(tokens):  # Iterate from the end of the list
#         if token.endswith(','):  # Check if the token ends with a comma
#             count += 1
#         else:
#             break  # Stop counting when a token without a comma is encountered
#     return count


def process_tokens(tokens: list[str]) -> list[str]:
    """
    Example:
        >>> tokens = ["select", "name,", "address,", "id", "from"]
        >>> process_tokens(tokens)
        ["select", "id", "from"]

        >>> tokens = ["select", "name,", "age"]
        >>> process_tokens(tokens)
        ["select", "age"]
    """
    i = 0
    while i < len(tokens):
        if tokens[i].endswith(','):  # Check if the current token ends with ','
            # Find the end of the consecutive comma tokens
            j = i
            while j < len(tokens) and tokens[j].endswith(','):
                j += 1

            # If a non-comma token is found after the comma tokens, replace the group with the last non-comma token
            if j < len(tokens):
                tokens[i:j + 1] = [tokens[j]]  # Replace the group with the last non-comma token
            else:
                tokens[i:j] = []  # If no non-comma token is found, remove the comma tokens
        else:
            i += 1  # Move to the next token

    return tokens


def find_suggestions(tokenized_queries: list[list[str]], completed_tokens: list[str], current_word: str, database_schema: dict[str, dict[str, list[str]]]) -> list[str]:
    """ Finds next possible words for autocompletion """
    #print(" List : ",completed_tokens)
    #creating object of score_manager.py file
    score = score_manage(database_schema)

    suggestions = list()
    #current_word = current_word.upper()

    for tokens in tokenized_queries:
        next_token:str=''
        #token: each line [toknized]
        if len(tokens) > len(completed_tokens):

            completed_tokens = process_tokens(completed_tokens)
            #completed_tokens = [token[1:].upper() if len(token)>1 and token[0] == '(' else token for token in completed_tokens]
            #completed_tokens = [item for token in completed_tokens for item in (["(", token[1:].upper()] if token.startswith("(") and len(token) > 1 else [token])]

            #print("List",completed_tokens)
            #I will check if previous word is ending with ',' or not if yes then same types of sugestions hould show without increase index in search
            # if completed_tokens and completed_tokens[-1].endswith(','):
            #     no_mul_tokens:int = count_consecutive_tokens_ending_with_comma_from_end(completed_tokens)

            #     completed_tokens = completed_tokens[:len(completed_tokens)-no_mul_tokens]

                # if is_token_matched_without_variables(tokens,completed_tokens[:len(completed_tokens)-no_mul_tokens]):
                #     next_token:list[str] = tokens[len(completed_tokens)-no_mul_tokens]
                #     print(next_token)
                

            #here it should be modified...[filed1]...[value]..[table] should be ignore in tokenized_quries 
            #print(f"\n{is_token_matched_without_variables(tokens,completed_tokens)}")
            #if tokens[:len(completed_tokens)] == completed_tokens:
            if is_token_matched_without_variables(tokens, completed_tokens):
                next_token:str = tokens[len(completed_tokens)]

                # If it's a placeholder, allow user to type anything and still suggest the next keyword
                #if is_placeholder(next_token):
                #    next_token = "[value]"  # Show a generic placeholder instead

                
                '''
                if suggested_tables:
                    print(" Here")
                    # If suggestActualTable returns a list, add all valid items
                    if isinstance(suggested_tables, list):
                        for token in suggested_tables:
                            if isinstance(token, str) and (token.startswith(current_word) or is_placeholder(token)):
                                suggestions.add(token)
                    elif isinstance(suggested_tables, str):
                        if suggested_tables.startswith(current_word) or is_placeholder(suggested_tables):
                            suggestions.add(suggested_tables)
                '''

            # Suggest only if it starts with current_word
            if next_token.startswith(current_word.upper()) or is_placeholder(next_token):
                suggestions.append(next_token)

                #if '[FIELD]' in suggestions and '[TABLE];' in suggestions and '[FIELD]' in suggestions:
                #    #print("THat is")
                #    print(f"\n{tokens}\n")    



    suggestions = remove_duplicates(suggestions)

    #if any token is alreay is completed then it can't be place imidiate after that
    #it will return rest suggestions
    # Remove immediate used tokens
    suggestions = remove_immidiate_used_token_from_suggestion(completed_tokens, suggestions)

    # Ensure we get actual table names instead of [TABLE]
    suggestions = suggestActualTable(suggestions, database_schema.keys())

    # Ensure we get actal fileds name instead of [FILED]
    #first we need to make it in form : dict[str:list[str]] from dict[str:dict[str:list[str]]]
    new_schema = { _table: list(_field.keys()) for _table, _field in database_schema.items() }
    suggestions = suggestActualFields(suggestions, new_schema)                             

    suggestions = suggestSubqueries(suggestions) #it will give suggestion of select .. starting sub queries...
    
    #rearranging accorind thier score of  most uses
    #suggestions = score.arrangeSuggestions(suggestions)

    #print(f"\nCompleted token list : {completed_tokens}")

    #print(f"\nCurrent word : {current_word}")
    if completed_tokens and not current_word: #and completed_tokens[-1] in suggestions:
        #print(f"last used token : {completed_tokens[-1]}")
        score.updateScore(completed_tokens[-1])

    #print("Current : ",current_word)
    index=0
    for suggestion in suggestions:
        if suggestion and suggestion.startswith(current_word) or suggestion.startswith(current_word.upper()):
            suggestions[index]=suggestion
            index+=1



    return suggestions[:index] if suggestions else []
    


# def remove_token_sequences(complete_tokens, remove_list):
#     #print("function called")
#     #print("stack:",remove_list)
#     for pattern in remove_list:
#         #print("fucntion runiing..")
#         # Convert both lists to strings for easier pattern matching
#         tokens_str = ' '.join(complete_tokens)
#         pattern_str = ' '.join(pattern)
        
#         # Find the index of the pattern
#         index = tokens_str.find(pattern_str)
#         if index != -1:
#             # If found, split the string and reconstruct without the pattern
#             before = tokens_str[:index].strip()
#             after = tokens_str[index + len(pattern_str):].strip()
#             tokens_str = before + ' ' + after
#             # Convert back to list
#             complete_tokens = [token for token in tokens_str.split(' ') if token]
#     #print("function end")
#     return complete_tokens


def remove_token_sequences(complete_tokens, remove_list):
    # Ensure remove_list is a list of sequences (even if single tokens)
    if not all(isinstance(item, list) for item in remove_list):
        remove_list = [ [item] if not isinstance(item, list) else item for item in remove_list ]
    
    for pattern in remove_list:
        n = len(pattern)
        m = len(complete_tokens)
        for i in range(m - n + 1):
            if complete_tokens[i:i+n] == pattern:
                complete_tokens = complete_tokens[:i] + complete_tokens[i+n:]
                break  # Remove only the first occurrence
    return complete_tokens






class SQLCompleter(Completer):
    def __init__(self, tokenized_queries:list[list[str]],database_schema)->None:
        self.tokenized_queries = tokenized_queries
        self.database_schema = database_schema
        self.show_all_tables = True  # Track whether to show all tables
        self.show_all_fields = True  # Track whether to show all fields
        self.show_all_functions = True  # Track whether to show all functions
        self.context_stack = []
        self.stack_item = -1
        self.query_type = 'UNKNOWN' #DDL: create drop,  DML: insert update delete, DQL: select, TCL: grant revoke
    
    
    # Function to format suggestions within terminal width
    def format_suggestions(self,label, items):
        if not items:
            return None
        suggestion_text = f"{label}: " + " ".join(f"[{item}]" for item in items)
        return suggestion_text[:terminal_width]  # Trim if exceeding width


    


    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        #print(f"({text_before_cursor})")

        last_space_pos = text_before_cursor.rfind(' ')
        
        #print(f"last_space : {last_space_pos}")
        # if last_space_pos != -1:
        #     #Here means user typs a space 
        #     text_before_cursor = text_before_cursor.replace(', ',',')
        #     last_space_pos = text_before_cursor.rfind(' ')

            # if ',' in text_before_cursor:
            #     print(text_before_cursor)
            # if text_before_cursor[-2] == ',':
            #     text_before_cursor = text_before_cursor[:-1]
            #     last_space_pos = text_before_cursor.rfind(' ')
            #     print(text_before_cursor)
        
        #print(f"last_space : {last_space_pos}")
        
        if last_space_pos == -1:
            completed_tokens = []
            current_word = text_before_cursor
        else:
            completed_part = text_before_cursor[:last_space_pos]
            completed_tokens = completed_part.split()

            #remove previous completed token forn=m now on which is already pushed to teh stack
            current_word = text_before_cursor[last_space_pos+1:]
        


        #print(completed_tokens)
        #if 'SELECT' in completed_tokens : print(" Before : ",completed_tokens)
        completed_tokens = [item for token in completed_tokens for item in (["(", token[1:].upper()] if token.startswith("(") and len(token) > 1 else [token])]
        #print(completed_tokens)

        # if self.context_stack:
        #     if completed_tokens:
        #         # Flatten self.context_stack into a single list
        #         flattened_context = []
        #         for sublist in self.context_stack:
        #             flattened_context.extend(sublist)
        #         # Remove items from the front of completed_tokens that are present in flattened_context
        #         index = 0
        #         while index < len(completed_tokens) and index < len(flattened_context) and completed_tokens[index] == flattened_context[index]:
        #             index += 1
        #         # Slice completed_tokens to remove the matching items from the front
        #         completed_tokens = completed_tokens[index:]
        #     else:
        #         self.context_stack.clear()
        
        #print(completed_tokens)

        #print("COMPLETE : ",completed_tokens)
        #print("Items : ",self.stack_item)
        if self.stack_item > -1:
            #It means subquery is added
            #print("POP: ",self.context_stack[self.stack_item])
            completed_tokens = remove_token_sequences(completed_tokens,self.context_stack[:self.stack_item+1])
        elif self.context_stack:
            completed_tokens = self.context_stack[0] + remove_token_sequences(completed_tokens,self.context_stack)
            #nned to clean the stack()
            ...

        #print("COMPLETE2 : ",completed_tokens)
        #print("STACk : ",self.context_stack)

        #detect which type of query is tyeping by user
        if completed_tokens:
            first_token = completed_tokens[0].upper()
            if first_token == 'SELECT':
                self.query_type = 'DQL'  # Data Query Language
            elif first_token in ('DELETE', 'UPDATE', 'INSERT'):
                self.query_type = 'DML'  # Data Manipulation Language
            #elif first_token in ('CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'COMMENT', 'RENAME'):
            #    self.query_type = 'DDL'  # Data Definition Language
            #elif first_token in ('GRANT', 'REVOKE'):
            #    self.query_type = 'DCL'  # Data Control Language
            #elif first_token in ('COMMIT', 'ROLLBACK', 'SAVEPOINT', 'SET TRANSACTION'):
            #    self.query_type = 'TCL'  # Transaction Control Language
            else:
                self.query_type = 'UNKNOWN'  # For any unclassified or incorrect commands
        else:
            self.query_type = 'UNKNOWN'
        #print(self.query_type)

       
        

        if len(completed_tokens)>=2:
            # Detect if we are entering a subquery (e.g., after '(' and 'SELECT')
            if '(' in completed_tokens[-2] and 'SELECT' in completed_tokens[-1]:
                # Push the outer query context onto the stack
                self.context_stack.append(completed_tokens[:-1])
                self.stack_item += 1
                #print("Inserted: ",completed_tokens[:-1])
                # Reset completed_tokens for the subquery
                completed_tokens = [completed_tokens[-1]]
                #print(completed_tokens)

        #if 'SELECT' in completed_tokens : print(" After : ",completed_tokens)

        # If we are exiting a subquery (e.g., after ')'), restore the outer query context
        if ')' in completed_tokens and self.context_stack and self.stack_item > -1:
            current_query = completed_tokens
            completed_tokens = self.context_stack[self.stack_item]
            self.stack_item -= 1
            self.context_stack.append(current_query)
            print("Subquery ended and item index: ",self.stack_item)
            #completed_tokens  = self.context_stack.pop
        #print("\nList : ", completed_tokens)

        #if 'SELECT' in completed_tokens : print(" Get_completeing : ",completed_tokens)

        suggestions = find_suggestions(self.tokenized_queries, completed_tokens, current_word,self.database_schema)
        
        
        #print(f"\n{suggestions}")

        #for suggestion in suggestions:  # Limit suggestions
        #    yield Completion(suggestion, start_position=-len(current_word))




        #########################################################################################################################################################

        # tables = []
        # fields = []
        # functions = []
        
        # for suggestion in suggestions:
        #     if suggestion in self.database_schema:  # If it's a table name
        #         tables.append(suggestion)
        #     elif any(suggestion in columns for columns in self.database_schema.values()):  # If it's a field name
        #         fields.append(suggestion)
        #     else:  # Otherwise, assume it's a function
        #         functions.append(suggestion)

        # # If there are any categorized suggestions, display only those
        # if tables or fields or functions:
        #     if tables:
        #         yield Completion(f"TBL: {' '.join(f'[{t}]' for t in tables[:6])}", start_position=-len(current_word), display_meta="Category")
        #     if fields:
        #         yield Completion(f"FLD: {' '.join(f'[{f}]' for f in fields[:6])}", start_position=-len(current_word), display_meta="Category")
        #     if functions:
        #         yield Completion(self.format_suggestions("FUN", functions[:6]), start_position=-len(current_word), display_meta="Category")
        #         #yield Completion(f"FUN: {' '.join(f'[{func}]' for func in functions)}", start_position=-len(current_word), display_meta="Category")
        # else:
        #     # If no category is needed, yield individual suggestions
        #     for suggestion in suggestions:
        #         yield Completion(suggestion, start_position=-len(current_word))

        #########################################################################################################################################################

        tables = []
        fields = []
        functions = []

        for suggestion in suggestions:
            if suggestion in self.database_schema:  # If it's a table name
                tables.append(suggestion)
            elif any(suggestion in columns for columns in self.database_schema.values()):  # If it's a field name
                fields.append(suggestion)
            else:  # Otherwise, assume it's a function
                functions.append(suggestion)

        score = score_manage(self.database_schema)

        # If there are any categorized suggestions, display only those
        if tables or fields or functions:
            if tables:
                #for table in score.arrangeSuggestions(tables)[:8]:
                #    yield Completion(table, start_position=-len(current_word), style="bg:lightpink", selected_style="fg:white bg:blue", display_meta="Table")
                #yield Completion(text="[More]", style="bg:lightpink", selected_style="fg:white bg:blue", display_meta="More Tables") 


                if self.show_all_tables:
                    # Show all tables if "More" was selected
                    for table in score.arrangeSuggestions(tables):
                        yield Completion(table, start_position=-len(current_word), style="bg:lightpink", selected_style="fg:white bg:blue", display_meta="Table",)
                else:
                    # Show only the first 8 tables
                    for table in score.arrangeSuggestions(tables)[:8]:
                        yield Completion(table,start_position=-len(current_word),style="bg:lightpink",selected_style="fg:white bg:blue",display_meta="Table")
                    # Add "[More]" option
                    yield Completion(text="[More]",start_position=-len(current_word),style="bg:lightpink",selected_style="fg:white bg:blue",display_meta="More Tables")
            
            if fields:
                #for field in score.arrangeSuggestions(fields)[:8]:
                #    yield Completion(field, start_position=-len(current_word), style="bg:lightblue", selected_style="fg:white bg:blue", display_meta="Field" )
                #yield Completion(text="[More]", style="bg:lightblue", selected_style="fg:white bg:blue", display_meta="More Fields") 

                if self.show_all_fields:
                    # Show all tables if "More" was selected
                    for field in score.arrangeSuggestions(fields):
                        yield Completion(field, start_position=-len(current_word), style="bg:lightblue", selected_style="fg:white bg:blue", display_meta="Field",)
                else:
                    # Show only the first 8 tables
                    for field in score.arrangeSuggestions(fields)[:8]:
                        yield Completion(field,start_position=-len(current_word),style="bg:lightblue",selected_style="fg:white bg:blue",display_meta="Field")
                    # Add "[More]" option
                    yield Completion(text="[More]",start_position=-len(current_word),style="bg:lightblue",selected_style="fg:white bg:blue",display_meta="More Fileds")
            
            
            
            if functions:
                #for func in score.arrangeSuggestions(functions)[:8]:
                #    yield Completion(func, start_position=-len(current_word), style="bg:lightgreen",selected_style="fg:white bg:blue", display_meta="Function" )
                #yield Completion(text="[More]", style="bg:lightgreen", selected_style="fg:white bg:blue", display_meta="More Functions") 
                if self.show_all_functions:
                    for function in score.arrangeSuggestions(functions):
                        yield Completion(function, start_position=-len(current_word), style="bg:lightgreen", selected_style="fg:white bg:blue", display_meta="Function",)
                else:
                    # Show only the first 8 tables
                    for function in score.arrangeSuggestions(functions)[:8]:
                        yield Completion(function,start_position=-len(current_word),style="bg:lightgreen",selected_style="fg:white bg:blue",display_meta="Function")
                    # Add "[More]" option
                    yield Completion(text="[More]",start_position=-len(current_word),style="bg:lightgreen",selected_style="fg:white bg:blue",display_meta="More functions")
            
        else:
            # If no category is needed, yield individual suggestions
            for suggestion in suggestions:
                yield Completion(suggestion, start_position=-len(current_word))
                
        #########################################################################################################################################################
























#runtime correction 
def runtime_monitor(text,completer:SQLCompleter)->bool:
    response=False
    #print(f"Validating: {text}")  # Debugging: Print the input text
    
    # Check if '[More]' is typed
    if '[More]' in text:
        #print("state varibale can be change")
        #print(f"\nchanging state variables {completer.query_type}")
        # Update the state to show all suggestions
        if completer.show_all_tables == False:
            completer.show_all_tables = True
        elif completer.show_all_fields == False:
            completer.show_all_fields = True
        elif completer.show_all_functions == False:
            completer.show_all_functions = True
        #print(f"\nchanging state variables {completer.show_all_fields}")
        
    else:
         # Update the state to show all suggestions
        if completer.show_all_tables == True:
            completer.show_all_tables = False
        elif completer.show_all_fields == True:
            completer.show_all_fields = False
        elif completer.show_all_functions == True:
            completer.show_all_functions = False
        #print(f"\nchanging state variables {completer.show_all_fields}")
        
    
    # Check if the query starts with a valid keyword
    valid_keywords = ['!', 'SELECT', 'INSERT', 'UPDATE', 'DELETE','CREATE','ALTER','DROP','TRUNCATE','COMMIT','EXIT']
    return any(text.upper().startswith(kw) for kw in valid_keywords)




# Custom key bindings for real-time modification    
bindings = KeyBindings()

@bindings.add('(')
def add_space_after_open_paren(event):
    """Add a space after '('"""
    buffer = event.app.current_buffer
    #print(">" , buffer.cursor_position)
    if len(buffer.text)>=2 and buffer.text[-1] == ' ' and buffer.text[-2] == '=':         
        buffer.insert_text('(')
    elif len(buffer.text)>=1 and buffer.text[-1] == '=':   
        buffer.insert_text(' ')
        buffer.insert_text('(')
    else:
        buffer.insert_text('(')

    buffer.cursor_position = len(buffer.text)


@bindings.add(' ')
def prevent_repeated_spaces(event):
    buffer = event.app.current_buffer
    # Check if the last character is already a space
    #if buffer.text and buffer.text[-1] ==  ',':
    #    return
        
    if buffer.text and buffer.text[-1] == ' ':
        # If the last character is a space, don't insert another space
        return
        ...
    # Otherwise, allow space to be inserted
    buffer.insert_text(' ')
    buffer.cursor_position = len(buffer.text)


@bindings.add(',')
def remove_space_before_coma(event):
    """Add a space after '('"""
    buffer = event.app.current_buffer
    #print(">" , buffer.cursor_position)
    if buffer.text and buffer.text[-1] == ' ': 
        buffer.delete_before_cursor(1)  # Remove the space
        buffer.insert_text(',')
    else:
        buffer.insert_text(',')

    buffer.cursor_position = len(buffer.text)




# @bindings.add('enter')
# def check_before_hit_enter(event):
#     buffer = event.app.current_buffer
#     # Check if the last character is already a space
#     if buffer.text and buffer.text[-1] != ';':
#         buffer.insert_text(';')
#     buffer.validate_and_handle()























def main()->None:

    dobj=serverConnect() #It should be first
    database_schema = dobj.fetch_database_structure() #It should be second
    
    #Optional
    #for table,desc in database_schema.items():
    #   print(f"\n{table}: {desc}")
    
    queries = read_queries("Query_files/generalize_queries2.txt") #It shoud be third
    tokenized_queries = tokenize_queries(queries) #It should be forth
    #print(tokenized_queries)

    #print("\nStart typing your SQL query (Ctrl+C to exit):")

    completer = SQLCompleter(tokenized_queries,database_schema) #It should be Fifth




    # Define a custom style
    custom_style = Style.from_dict({
        # Customize the prompt appearance
        #"prompt": "bg:#008787 #eeeeee",  # Green background with white text
        "prompt": "bg:#1e1e1e #06989a",
        #"completion-menu.completion": "bg:#008800 #ffffff",  # Darker green for completions
        #"completion-menu.completion.current": "bg:#00ff00 #000000",  # Bright green for selected completion
        #"scrollbar.background": "bg:#00aa00",  # Green scrollbar background
        #"scrollbar.button": "bg:#00ff00",  # Bright green scrollbar button
    })

    # Validator for basic SQL syntax
    sql_validator = Validator.from_callable(
        lambda text: runtime_monitor(text, completer), 
        error_message='Must start with !/SELECT/INSERT/UPDATE/DELETE/DROP/TRUNCATE/CREATE/ALTER/COMMIT',
        move_cursor_to_end=True
    )
    #object of getChacater t get chracater on UI
    cobj = getChracter()




    while True:
        try:
            user_input = prompt(
                "╭─"+ cobj.chracter() + dobj.host+'@'+dobj.user + "\n╰─➤ $ ",
                rprompt=" " * 50,  # Add 10 spaces of padding on the right
                completer= completer,
                complete_style=CompleteStyle.MULTI_COLUMN,
                complete_while_typing=True,  # Enable completions while typing
                #multiline=True,
                #prompt_continuation=lambda width, line_number, is_soft_wrap: "... ",
                #mouse_support=True,  # Enable mouse support
                history=FileHistory("history.txt"),
                style=custom_style,
                validator=sql_validator,
                validate_while_typing=True,
                key_bindings=bindings
            )

            #run os commands directly with ! Ex: !ls
            if user_input.startswith('!'):
                os.system(user_input[1:])
                print()
                continue

            #exit for exit
            if user_input.lower() == 'exit':
                break


            print(f"You typed: {user_input}")
            
            final_query = checkSyntax(user_input,database_schema)

            if final_query is None:
                print("Syntax check failed. Query is None.")
                continue
            print(f"Final : {final_query}")

            out = showOutput(dobj.runQuery(final_query))                
            out.display()
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
    ... 






