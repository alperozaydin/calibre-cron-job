include .env

IMAGE_NAME=calibre-cron-job
TAG=latest
CONTAINER_NAME=calibre-cron-job
PORT=5000
AWS_REGION=eu-central-1


init:
	poetry config virtualenvs.in-project true

install: init
	poetry install
	poetry export -f requirements.txt --output requirements.txt --without-hashes

lock:
	poetry lock

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

build-no-cache:
	docker build --no-cache -t $(IMAGE_NAME):$(TAG) .

run: clean
	docker run --name $(CONTAINER_NAME) -p $(PORT):$(PORT) -v ./calibre_cron_job/main.py:/app/main.py -d $(IMAGE_NAME):$(TAG)
	docker logs -f $(CONTAINER_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

clean:
	docker system prune -f

tag:
	docker tag $(IMAGE_NAME):$(TAG) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(TAG)

push: tag
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(TAG)

logs:
	docker logs -f $(CONTAINER_NAME)

kill:
	docker kill $(CONTAINER_NAME)

synth:
	poetry run cdk synth --app "python cdk/app.py"


deploy:
	poetry run cdk deploy --app "python cdk/app.py"

bootstrap:
	poetry run cdk bootstrap aws://$(AWS_ACCOUNT_ID)/$(AWS_REGION)