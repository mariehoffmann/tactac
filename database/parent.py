# given db connection and cursor, and a taxid as (level, taxid) return the parent
# node (level+1, par(taxid))
def parent(con, cur, node):
    cur.execute("SELECT parent_tax_id FROM node WHERE tax_id = {}".format(node[1]))
    con.commit()
    row = cur.fetchone()
    if row is None:
        print("Missing key ({}) in table node".format(node[1]))
        sys.exit()
        #return None
    else:
        return (node[0] + 1, row[0]) # or just row?
