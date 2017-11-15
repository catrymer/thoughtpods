from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ThoughtPod, PodItem
app = Flask(__name__)


engine = create_engine('sqlite:///thoughtpods.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/hello')
def HelloWorld():
    return "Hello World"

@app.route('/pods/<int:pod_id>/')
def podList(pod_id):
    thoughtpod = session.query(ThoughtPod).filter_by(id=pod_id).one()
    items = session.query(PodItem).filter_by(thought_pod_id=thoughtpod.id)
    output = '<h1>'
    output += thoughtpod.pod_title
    output += '</h1><br>'
    for i in items:
        output += i.title
        output += '</br>'
        output += i.url
        output += '</br>'
        output += i.description
        output += '</br>'
        output += '</br>'
    return output

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
