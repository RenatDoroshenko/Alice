
# def store_experience(summary, experience):
#     experience_entry = Experience(summary=summary, experience=str(experience))
#     db.session.add(experience_entry)
#     db.session.commit()


# def retrieve_experience(summary, k=1):
#     experiences = Experience.query.all()
#     summaries = [e.summary for e in experiences]
#     summary_vectors = model.encode(summaries)

#     query_vector = model.encode([summary])[0]

#     index = faiss.IndexFlatL2(dimension)
#     index.add(np.array(summary_vectors, dtype=np.float32))
#     _, indices = index.search(np.array([query_vector], dtype=np.float32), k)
#     return [eval(experiences[i].experience) for i in indices[0]]
