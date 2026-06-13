# check_category_selection function. Check categories against the category selection table
# This function takes transaction description, category and overwrite? and returns category
# If no category is provided it simply searches the category rules table for that description
# and returns the suggested category if found. If a category is provided it searches category_rules
# and if no matching description is found it appends the table with that description and category
# if it is found then it returns that "existing" category.
# Note this function does not commit. Caller commits

def category_rule_check(db, description, category=None, overwrite=False):
    # Check that description, category, and overwrite are not null(or None?) and correct data type
    # if not return raise "invalid call"


    # Search for description in db category_rules


    # if description found return category of found description


    # if no description found add description to the rules table and return "None"


    pass  # placeholder so the skeleton compiles - remove when implementing
