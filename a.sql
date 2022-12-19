# asso + right join subq 이후 outerjoin
SELECT tags.name, coalesce(anon_1.count_1, :coalesce_1) AS count, coalesce(anon_1.sum_1, :coalesce_2) AS sum
FROM tags
         LEFT OUTER JOIN (SELECT posttags.tag_id                      AS tag_id,
                                 count(posttags.post_id)              AS count_1,
                                 sum(CAST(posts.has_type AS INTEGER)) AS sum_1
                          FROM posttags
                                   JOIN posts ON posts.id = posttags.post_id
                          GROUP BY posttags.tag_id) AS anon_1 ON tags.id = anon_1.tag_id
ORDER BY anon_1.count_1 DESC
LIMIT :param_1

# left.right관계명으로 outerjoin query비교
SELECT tags.name, coalesce(count(posts.id), :coalesce_1) AS count, sum(CAST(posts.has_type AS INTEGER)) AS sum
FROM tags
         LEFT OUTER JOIN (posttags AS posttags_1 JOIN posts ON posts.id = posttags_1.post_id)
                         ON tags.id = posttags_1.tag_id
GROUP BY tags.id
ORDER BY count DESC
LIMIT :param_1


