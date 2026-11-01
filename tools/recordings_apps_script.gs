/**
 * Saves practice recordings from the Guitar app into your Google Drive.
 *
 * Why: Google doesn't let service accounts own files in a personal Drive, so the app sends the
 * recording here and this script (running as you) saves it into your folder.
 *
 * Setup (once, ~3 minutes):
 *  1. Go to https://script.google.com -> New project. Paste this whole file in, replacing what's there.
 *  2. Set TOKEN below to the same value as `recordings_token` in the app's secrets.
 *  3. Deploy -> New deployment -> type "Web app".
 *       Execute as: Me      Who has access: Anyone
 *     Deploy, allow the permissions it asks for (Drive), and copy the Web app URL.
 *  4. Put the URL in the app's secrets as `recordings_script_url`.
 */

const FOLDER_ID = '1rOnT56I9lOWavdKoWv9Np8atuxSiUsQP';
const TOKEN = 'PASTE-THE-SAME-TOKEN-AS-IN-THE-APP-SECRETS';

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.token !== TOKEN) return reply({ error: 'bad token' });
    const blob = Utilities.newBlob(Utilities.base64Decode(body.data), body.mime || 'audio/wav', body.name);
    const file = DriveApp.getFolderById(FOLDER_ID).createFile(blob);
    return reply({ id: file.getId(), url: file.getUrl() });
  } catch (err) {
    return reply({ error: String(err) });
  }
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
