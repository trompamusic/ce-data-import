TODAY := $(shell date +'%Y-%m-%d')
build:
	docker build -t mtgupf/verovio:$(TODAY) .

push:
	docker push mtgupf/verovio:$(TODAY)

all: build push

.PHONY: build push