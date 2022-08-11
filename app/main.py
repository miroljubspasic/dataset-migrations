import click


@click.group()
def cli():
    """This script run fetch data lists from (pagination) api. """
    pass


@cli.command(context_settings={"ignore_unknown_options": True})
@click.option('--type',
              type=click.Choice(['customers', 'orders', 'giftcards', 'sor_subscriptions', 'sor_orders']))
def start(datatype):
    """Download data from API endpoint."""
    if datatype is None:
        click.echo("Try 'migration start --help' for help")
        exit()
    click.echo('Continue? [yn] ', nl=False)
    c = click.getchar()
    click.echo()
    if c == 'y':
        click.echo('We will go on')
        click.echo(click.style(f'Start fetch data for {datatype} endpoint', bg="green"))
        module = __import__('dataset')
        class_name = datatype.replace("_", " ").title().replace(" ", "")
        class_ = getattr(module, class_name)
        job = class_()
        jobStatus = job.init_job()
        if jobStatus['state'] == 'exists':
            click.echo(
                f'There is already started job {jobStatus["id"]} with id.')
            click.echo(
                f'Press y to continue with job {jobStatus["id"]} or n to cancel job and run migration again ')
            click.echo('Continue? [yn] ', nl=False)
            c = click.getchar()
            click.echo()
            if c == 'n':
                job.cancel_job({'id': jobStatus["id"], 'status': 'aborted'})
                # init new job
                jobStatus = job.init_job()
                job.run_job_main(jobStatus)
            elif c == 'y':
                job.run_job_main(jobStatus)

            else:
                click.echo('Invalid input :(')
        else:
            click.echo(f'Starting with new job {jobStatus["id"]}')
            job.run_job_main(jobStatus)

    elif c == 'n':
        click.echo('Abort!')
    else:
        click.echo('Invalid input :( ')
