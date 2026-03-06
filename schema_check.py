from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://140.169.17.180:7687', auth=('neo4j', 'graph_admin'))
with d.session() as s:
    # Skill keys
    recs = list(s.run('MATCH (sk:Skill) RETURN keys(sk) as keys LIMIT 1'))
    print('SKILL KEYS:', recs[0]['keys'] if recs else 'NONE')

    # JobReq keys
    recs2 = list(s.run('MATCH (j:JobReq) RETURN keys(j) as keys LIMIT 1'))
    print('JOBREQ KEYS:', recs2[0]['keys'] if recs2 else 'NONE')

    # Employee->Skill rel
    recs3 = list(s.run('MATCH (e:Employee)-[rel]->(sk:Skill) RETURN type(rel) as reltype, keys(rel) as relkeys LIMIT 1'))
    print('EMP->SKILL REL:', dict(recs3[0]) if recs3 else 'NONE')

    # Counts
    emp_cnt = list(s.run('MATCH (e:Employee) RETURN count(e) as cnt'))[0]['cnt']
    skl_cnt = list(s.run('MATCH (sk:Skill) RETURN count(sk) as cnt'))[0]['cnt']
    jr_cnt = list(s.run('MATCH (j:JobReq) RETURN count(j) as cnt'))[0]['cnt']
    print(f'Employees: {emp_cnt}, Skills: {skl_cnt}, JobReqs: {jr_cnt}')

    # OpenReq sample
    recs4 = list(s.run('MATCH (j:OpenReq) RETURN keys(j) as keys LIMIT 1'))
    print('OPENREQ KEYS:', recs4[0]['keys'] if recs4 else 'NONE')

    # Job keys
    recs5 = list(s.run('MATCH (j:Job) RETURN keys(j) as keys LIMIT 1'))
    print('JOB KEYS:', recs5[0]['keys'] if recs5 else 'NONE')

    # Check vector indexes
    recs6 = list(s.run('SHOW INDEXES YIELD name, type WHERE type = "VECTOR" RETURN name'))
    print('VECTOR INDEXES:', [r['name'] for r in recs6])

d.close()
print("DONE")
