# category_rule_check function. 

def category_rule_check(db, description, category_id, overwrite=False):
    # Check that description, category, and overwrite are not null(or None?) and correct data type
    # if not return raise "invalid call"
    
    if not isinstance(description, str) or not description:
        raise ValueError("Invalid description. Must be a non-empty string.")
    if not isinstance(category_id, int) or category_id < 1:
        raise ValueError("Invalid category id. Must be a non-empty integer if provided.")
    if not isinstance(overwrite, bool):
        raise ValueError("Invalid overwrite flag. Must be a boolean.")


    # Search for description in db category_rules
    result = db.execute("SELECT category_id FROM categorization_rules WHERE description_pattern = ?", (description,))
    row = result.fetchone()

    # if description found return category of found description
    # if it is different from the proposed category and the overwrite is True it returns the proposed
    # category_id and updates the categorization rules.
    if row:
        if row[0] == category_id:
            return row[0]
        else:
            if not overwrite:
                return row[0]
            else:
                db.execute("UPDATE categorization_rules SET category_id = ? WHERE description_pattern = ?", (category_id, description))
                return category_id
            
    # if no description found add description to the rules table and return the proposed category_id
    db.execute("INSERT INTO categorization_rules (description_pattern, category_id) VALUES (?, ?)", (description, category_id))
    return category_id


