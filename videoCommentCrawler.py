# Ketao Yin
# YouTube Video Comment Crawler

#!/usr/bin/python

import sys
import json
import csv

import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# DEFAULT DATASIZE PARAMETERS
maxCommentsPerVideo = 2000

# CUSTOM DATASIZE PARAMETERS
if len(sys.argv) >= 3:
	param1 = sys.argv[2]

	if param1.isdigit() and int(param1) > 0:
			maxCommentsPerVideo = int(param1)

# Variables
userInput = sys.argv[1]
commentThreadPart = 'snippet'

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Authorize the request and store authorization credentials.
def get_authenticated_service():
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
	credentials = flow.run_console()
	return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def comment_threads_list_by_video_id(service, **kwargs):
	commentThreads = service.commentThreads().list(
		**kwargs
		).execute()

	return commentThreads

def comment_threads_all_items_by_video_id(service, **kwargs):
	commentThreads = service.commentThreads().list(
		**kwargs
		).execute()

	# Max number of pages to list
	itemsPerPage = len(commentThreads['items'])
	currPages = 1
	maxPages = maxCommentsPerVideo / itemsPerPage
	if maxCommentsPerVideo %  itemsPerPage != 0:
		maxPages+=1

	nextPageToken = commentThreads.get('nextPageToken')

	while ('nextPageToken' in commentThreads and currPages <= maxPages):
		nextPage = service.commentThreads().list(
			pageToken=nextPageToken,
			**kwargs
			).execute()
		commentThreads['items'] = commentThreads['items'] + nextPage['items']

		currPages+=1

		if 'nextPageToken' not in nextPage:
		    commentThreads.pop('nextPageToken', None)
		else:
		    nextPageToken = nextPage['nextPageToken']

	return commentThreads

# Main
if __name__ == "__main__":
	# Output file
    if sys.argv[1] is not "":
  		fileName = "comments-" + sys.argv[1] + ".csv"
	
    file = open(fileName,"w+")
    writer = csv.writer(file)

    service = get_authenticated_service()

    print("\n\n\n")
    print("Video ID: " + userInput)
    print("Max number of comments per video: " + str(maxCommentsPerVideo))
    print("\n")

  	# Finding video top level comments
    commentThreads = comment_threads_all_items_by_video_id(service,
  		part=commentThreadPart,
  		videoId=userInput)

    threads = commentThreads['items']

  	# Counter for comments collected from video
    commentsCount = 0

    for thread in threads:
		if (commentsCount < maxCommentsPerVideo):
	  		topLevelComment = thread['snippet']['topLevelComment']['snippet']['textOriginal']
	  		cleanedComment = topLevelComment.encode('utf-8').strip()
	  		updatedTime = thread['snippet']['topLevelComment']['snippet']['updatedAt']
	  		
	  		# Write to .csv file
	  		writer.writerow([cleanedComment, updatedTime])
	  		commentsCount+=1

	  	else:
	  		break

    file.close()
    print("Comment collection completed!")
    print("Max number of comments: " + str(maxCommentsPerVideo))
    print("Total number of comments collected: " + str(commentsCount))
