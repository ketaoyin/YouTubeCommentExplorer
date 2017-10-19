# Ketao Yin

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
maxComments = 5000
maxCommentsPerVideo = 100

# CUSTOM DATASIZE PARAMETERS
if len(sys.argv) >= 4:
	param1 = sys.argv[2]
	param2 = sys.argv[3]

	if param1.isdigit() and param2.isdigit():
		if int(param1) > 0 and int(param2) > 0:
			maxComments = int(param1)
			maxCommentsPerVideo = int(param2)

# Variables
userNameInput = sys.argv[1]
channelIdPart = 'snippet,contentDetails,statistics'
playlistItemsPart = 'contentDetails'
numVideos = 50
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


def channels_list_by_username(service, **kwargs):
	channelIList = service.channels().list(
		**kwargs
		).execute()

	if (channelIList['pageInfo']['totalResults'] == 0):
		print("ERROR: User not found.")
		sys.exit()

	return channelIList


def playlist_items_list_by_playlist_id(service, **kwargs):
	items = service.playlistItems().list(
		**kwargs
		).execute()

	return items


def playlist_all_items_by_playlist_id(service, **kwargs):
	items = service.playlistItems().list(
		**kwargs
		).execute()

	nextPageToken = items.get('nextPageToken')

	while ('nextPageToken' in items):
		nextPage = service.playlistItems().list(
			pageToken=nextPageToken,
			**kwargs
			).execute()
		items['items'] = items['items'] + nextPage['items']

		if 'nextPageToken' not in nextPage:
		    items.pop('nextPageToken', None)
		else:
		    nextPageToken = nextPage['nextPageToken']

	return items


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

    # Finding channel information, including Uploads playlistId
    channelInfo = channels_list_by_username(service,
	  	part=channelIdPart,
	  	forUsername=userNameInput)

    channelId = channelInfo['items'][0]['id']
    uploadsListId = channelInfo['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    print("\n\n\n")
    print(userNameInput + " ID: " + channelId)
    print(userNameInput + " Uploads Playlist ID: " + uploadsListId)
    print("Max number of comments: " + str(maxComments))
    print("Max number of comments per video: " + str(maxCommentsPerVideo))
    print("\n")

    # Find all videos in Uploads playlit
    uploadItems = playlist_all_items_by_playlist_id(service,
  		part=playlistItemsPart,
  		maxResults=numVideos,
  		playlistId=uploadsListId)
    
    items = uploadItems['items']

    # Counter for number of videos comments are collected from
    vidNum = 1
    # Counter for total comments collected from uploads playlist
    totalCommentsCount = 0

    # Find top level comments for each uploaded video
    for video in items:
  		vidId = video['contentDetails']['videoId']
  		print(str(vidNum) + ": " + vidId + "\n")

	  	commentThreads = comment_threads_all_items_by_video_id(service,
	  		part=commentThreadPart,
	  		videoId=vidId)

	  	threads = commentThreads['items']

	  	# Counter for comments collected from current video
	  	commentsCount = 0

		for thread in threads:
			if (totalCommentsCount < maxComments and commentsCount < maxCommentsPerVideo):
		  		topLevelComment = thread['snippet']['topLevelComment']['snippet']['textOriginal']
		  		cleanedComment = topLevelComment.encode('utf-8').strip()
		  		updatedTime = thread['snippet']['topLevelComment']['snippet']['updatedAt']
		  		
		  		# Write to .csv file
		  		writer.writerow([cleanedComment, updatedTime])
		  		totalCommentsCount+=1
		  		commentsCount+=1

		  	else:
		  		break

  		vidNum+=1

  		if (totalCommentsCount >= maxComments):
  			break

    file.close()
    print("Comment collection completed!")
    print("Max number of comments: " + str(maxComments))
    print("Total number of comments collected: " + str(totalCommentsCount))
