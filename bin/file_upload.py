    
@app.route('/search/<query>')
@app.route('/search/<query>/<delta>')
def search_all(query, delta=None):
    return "Search by query: %s" % query
    
@app.route('/community/<community>/search', methods=['GET', 'POST'])
def search_community(community):
    if not g.search_form.validate_on_submit():
        return redirect(url_for('community', community=community))
    if not request.form['community_search']:
        return redirect(url_for('search_all', query=request.form['search']))
    kwargs = {
        'community': community,
        'query': request.form['search'],
        'delta': dict(time_choices).get(g.search_form.time_search.data)
    }
    return redirect(url_for('search_community_results', **kwargs))
    
@app.route('/community/<community>/search/<query>')
@app.route('/community/<community>/search/<query>/<delta>')
def search_community_results(community, query, delta=0):
    c = Community.query.filter_by(name=community).first()
    if delta != 0:
       results = Posts.search_by_time_delta(
       Posts.search_by_community, delta, query, c
       )
    else:
        results = Posts.search_by_community(query, c)
    kwargs = {
        'community': community,
        'c': c,
        'results': results
    }
    return render_template('search_results.html', **kwargs)