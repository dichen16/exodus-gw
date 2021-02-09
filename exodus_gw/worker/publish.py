from os.path import basename

import dramatiq
from sqlalchemy.orm import Session

from exodus_gw.aws.dynamodb import write_batches
from exodus_gw.crud import get_publish_by_id
from exodus_gw.database import db_engine
from exodus_gw.settings import Settings


@dramatiq.actor
def commit(publish_id: str, env: str):
    settings = Settings()
    db = Session(bind=db_engine(settings))

    items = []
    last_items = []

    for item in get_publish_by_id(db, publish_id).items:
        if basename(item.web_uri) in settings.entry_point_files:
            last_items.append(item)
        else:
            items.append(item)

    items_written = False
    last_items_written = False

    if items:
        items_written = write_batches(env, items)

    if not items_written:
        # Delete all items if failed to write any items.
        write_batches(env, items, delete=True)
    elif last_items:
        # Write any last_items if successfully wrote all items.
        last_items_written = write_batches(env, last_items)

        if not last_items_written:
            # Delete everything if failed to write last_items.
            write_batches(env, items + last_items, delete=True)