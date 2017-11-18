from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ThoughtPod, PodItem
app = Flask(__name__)


engine = create_engine('sqlite:///thoughtpods.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/pods/')
def Home():
    allpods = session.query(ThoughtPod)
    return render_template('index.html', allpods=allpods)


@app.route('/pods/<int:pod_id>/')
def podList(pod_id):
    thoughtpod = session.query(ThoughtPod).filter_by(id=pod_id).one()
    items = session.query(PodItem).filter_by(thought_pod_id=thoughtpod.id)
    return render_template('podlist.html', thoughtpod=thoughtpod, items=items)


@app.route('/pods/new/', methods=['GET', 'POST'])
def newThoughtPod():
    if request.method == 'POST':
        newPod = ThoughtPod(pod_title=request.form['title'], description=request.form['description'])
        session.add(newPod)
        session.commit()
        return redirect(url_for('Home'))
    else:
        return render_template('newpod.html')


@app.route('/pods/<int:pod_id>/new/', methods=['GET', 'POST'])
def newPodListItem(pod_id):
    if request.method == 'POST':
        newItem = PodItem(
            title=request.form['title'], url=request.form['url'],
            description=request.form['description'], time_investment=request.form['time_investment'],
            difficulty_level=request.form['difficulty_level'], thought_pod_id=pod_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template('newpodlistitem.html', pod_id=pod_id)

@app.route('/pods/<int:pod_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editPodListItem(pod_id, item_id):
    editedItem = session.query(PodItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['url']:
            editedItem.url = request.form['url']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['time_investment']:
            editedItem.time_investment = request.form['time_investment']
        if request.form['difficulty_level']:
            editedItem.difficulty_level = request.form['difficulty_level']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template(
            'editpodlistitem.html', pod_id=pod_id, item_id=item_id, item=editedItem)


@app.route('/pods/<int:pod_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deletePodListItem(pod_id, item_id):
    itemToDelete = session.query(PodItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template('deletepodlistitem.html', item=itemToDelete)


# Add JSON endpoints
@app.route('/pods/JSON/')
def thoughtPodJSON():
    thoughtPods = session.query(ThoughtPod).all()
    return jsonify(thoughtPods=[i.serialize for i in thoughtPods])


@app.route('/pods/<int:pod_id>/JSON/')
def thoughtPodListJSON(pod_id):
    thoughtpod = session.query(ThoughtPod).filter_by(id=pod_id).one()
    allPodItems = session.query(PodItem).filter_by(thought_pod_id=thoughtpod.id).all()
    return jsonify(allPodItems=[i.serialize for i in allPodItems])


@app.route('/pods/<int:pod_id>/<int:item_id>/JSON/')
def podListItemJSON(pod_id, item_id):
    onePodItem = session.query(PodItem).filter_by(id=item_id).one()
    return jsonify(onePodItem=onePodItem.serialize)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
