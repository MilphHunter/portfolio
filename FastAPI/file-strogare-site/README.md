# Application For Storing And Downloading Files using Python FastAPI SQLite and HTML/CSS/JS

**It is a complete application for storing and sharing your files.**

Available functionality:

- Registration/Authorization (including via using session tokens)
- Adding files by administrator and uploading them from authorized users
- Convenient search by name as well as tags assigned to files
- Easy interaction with users, tags and files with the ability to delete, create and edit
- Easy download control: the ability to view your download history, number of downloads and more at any second!

## Registration page

![Login Page Dark](static/assets/readme/sign-up.jpg)
![Login Page Light](static/assets/readme/sign-up-light-theme.jpg)

**User Registration Page. It has 3 fields. 2 theme: light and dark. Also set up a lot of checks and in case something
went wrong, the user will be notified:**

![Login Page Error](static/assets/readme/sign-up-error.jpg)

## Login page

![Login Page Dark](static/assets/readme/sign-in.jpg)
![Login Page Light](static/assets/readme/login-light-theme.jpg)

**The page is similar to registration. Also set up a lot of checks and has 2 themes. If registration is successful, the user receives a session token.**

## Token and access rights

![Token](static/assets/readme/token.jpg)

**Upon successful authorization, the user is given a session token, which guarantees that actions
(such as downloading files) will not be performed by third-party users, and therefore - will not load traffic.
In addition to users, there is an administrator role. Unlike a user, he/she has access to the administration panel.
Below are the errors that the user sees in case of unauthorized access to the capabilities of authorized users, administrator:**

![Insert user error](static/assets/readme/insert-user-error.jpg)
![Insert admin error](static/assets/readme/insert-admin-error.jpg)

## Workspace

![Workspace Page Dark](static/assets/readme/workspace.jpg)
![Workspace Page Light](static/assets/readme/workspace-light-theme.jpg)

**If authorization is successful, the user enters the workspace. Here he can upload any non-hidden files.
If necessary, the files can be sorted by tags, as well as searched using the input on the top right:**

![Workspace Page Tag Sort](static/assets/readme/workspace-tags.jpg)

**The number next to the tag name is the number of files associated with it. If necessary, the user can select
several tags.**
**Also on the page there is a working pagination.**

## Admin Panel - Users

![Admin Panel Users](static/assets/readme/admin-user.jpg)

**In the users window, the administrator can view active users of the resource, their email, recent activity and the
number of uploaded files. If necessary, it is possible to ban a user (by blocking his email). In this case the
following pop-up window will appear:**

![Admin Panel Block User](static/assets/readme/admin-block-user.jpg)

## Admin Panel - Tags

![Admin Panel Tags](static/assets/readme/admin-tag.jpg)

**By clicking on the tags tab the user can see the names of tags, the number of files associated with them, the date of
creation and the number of downloads of files with a particular tag.**

![Admin Panel Add Tag](static/assets/readme/admin-add-tag.jpg)

**Creating new tag window.**

![Admin Panel Edit Tags](static/assets/readme/admin-edit-tag.jpg)

**Update tag window.**

![Admin Panel Delete Tags](static/assets/readme/admin-delete-tag.jpg)

**Delete tag window.**

![Admin Panel Search Tags](static/assets/readme/admin-search-tag.jpg)

**Also, all admin elements (not only tags) have a search option for more convenient interaction with elements.**

## Admin Panel - File

![Admin Panel File](static/assets/readme/admin-file.jpg)

**The file management panel allows the administrator to manage files. Here he can see file names, the number of
downloads of a particular file, the date it was added, and the file size. By clicking on the blue download button,
the administrator can see the download history of a particular file:**

![Admin Panel File Download History](static/assets/readme/admin-download-history.jpg)

**Here the administrator can see the name of the file at the time of upload (the name can be changed, but more on that
later), by whom the file was uploaded and the date of upload.**

![Admin Panel File Add](static/assets/readme/admin-add-file.jpg)

**The panel of adding a file looks as follows: file upload field, name - is determined automatically (the name of the
uploaded file), but can be changed immediately, tags - the first is assigned automatically - Image, Video, Audio or
Other, it can be removed, as well as add your own tags separated by comma. If the entered tag is absent in the
database, it will be automatically created and assigned to this file, status - if Active - visible to users,
Hidden - hidden.**

![Admin Panel File Edit](static/assets/readme/admin-file-edit.jpg)

**Update file window.**

![Admin Panel File Delete](static/assets/readme/admin-delete-tag.jpg)

**Delete file window.**

## Feedback

Please use [telegram](https://t.me/saw_TheMoon) for questions or comments :)
Thanks for your attention!!!
