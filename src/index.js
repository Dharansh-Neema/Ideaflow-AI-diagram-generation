const { Client } = require('@notionhq/client');

const notion = new Client({ auth: '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' });

(async () => {
  const pageId = '1f8e4db1914180329177d006eb1a8595';
  const response = await notion.pages.retrieve({ page_id: pageId });
  console.log(response);
})();